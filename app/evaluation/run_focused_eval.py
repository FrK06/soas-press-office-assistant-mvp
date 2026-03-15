from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any

from app.evaluation.common import (
    DATASET_PATH,
    EvalCase,
    OUTPUT_DIR,
    aggregate_metrics,
    evaluate_case,
    evaluate_dataset,
    jaccard_at_k,
    load_dataset,
    parse_expected_experts,
    select_cases,
)
from app.retrieval.expert_ranker import RankerConfig, ranker_config_to_dict


DEFAULT_FOCUSED_OUTPUT_DIR = Path('data/evaluation/focused')
PARAPHRASE_DATASET_PATH = Path('data/evaluation/benchmarks/paraphrase_eval_set_cleaned.csv')
BASELINE_RESULTS_PATH = OUTPUT_DIR / 'evaluation_results.json'
DEFAULT_THRESHOLD_KEY = 'single_0.55_final_0.62'

ABLATION_VARIANTS = {
    'variant_a_retrieval_only': {
        'label': 'Variant A: retrieval aggregation only',
        'config': RankerConfig(
            enable_topic_boosts=False,
            enable_media_signal_boost=False,
            enable_diversity_penalty=False,
        ),
    },
    'variant_b_topic_boosts': {
        'label': 'Variant B: retrieval aggregation plus topic boosts',
        'config': RankerConfig(
            enable_topic_boosts=True,
            enable_media_signal_boost=False,
            enable_diversity_penalty=False,
        ),
    },
    'variant_c_topic_and_media': {
        'label': 'Variant C: retrieval aggregation plus topic boosts and media-signal boost',
        'config': RankerConfig(
            enable_topic_boosts=True,
            enable_media_signal_boost=True,
            enable_diversity_penalty=False,
        ),
    },
    'variant_d_full_system': {
        'label': 'Variant D: full current system',
        'config': RankerConfig(
            enable_topic_boosts=True,
            enable_media_signal_boost=True,
            enable_diversity_penalty=True,
        ),
    },
}
FULL_VARIANT_KEY = 'variant_d_full_system'
THRESHOLD_GRID = [
    RankerConfig(min_single_chunk_score=min_single, min_final_score=min_final)
    for min_single in (0.55, 0.60, 0.65)
    for min_final in (0.57, 0.62, 0.67)
]
REQUIRED_PARAPHRASE_COLUMNS = {
    'source_test_id',
    'paraphrase_id',
    'paraphrase_level',
    'sender_name',
    'sender_email',
    'outlet_name',
    'subject',
    'body',
    'expected_experts',
}


@dataclass(frozen=True)
class ParaphraseCase:
    source_test_id: str
    paraphrase_id: str
    paraphrase_level: str
    sender_name: str
    sender_email: str
    outlet_name: str
    subject: str
    body: str
    expected_experts: list[str]


@dataclass(frozen=True)
class FocusedOutputPaths:
    output_dir: Path
    baseline_reference: Path
    e1_summary: Path
    e1_cases: Path
    e2_summary: Path
    e2_cases: Path
    e5_summary: Path
    e5_cases: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run the focused academic evaluation suite.')
    parser.add_argument('--dataset-path', type=Path, default=DATASET_PATH)
    parser.add_argument('--paraphrase-path', type=Path, default=PARAPHRASE_DATASET_PATH)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_FOCUSED_OUTPUT_DIR)
    parser.add_argument('--baseline-results-path', type=Path, default=BASELINE_RESULTS_PATH)
    parser.add_argument('--label', default='cleaned_default')
    return parser.parse_args()


def _build_output_paths(output_dir: Path) -> FocusedOutputPaths:
    return FocusedOutputPaths(
        output_dir=output_dir,
        baseline_reference=output_dir / 'baseline_reference.json',
        e1_summary=output_dir / 'e1_ablation_summary.json',
        e1_cases=output_dir / 'e1_ablation_case_results.csv',
        e2_summary=output_dir / 'e2_selective_prediction_summary.json',
        e2_cases=output_dir / 'e2_selective_prediction_case_results.csv',
        e5_summary=output_dir / 'e5_paraphrase_summary.json',
        e5_cases=output_dir / 'e5_paraphrase_case_results.csv',
    )


def _write_rows(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError(f'No rows available to write: {path}')
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _rank_value(rank: int | None) -> int:
    return rank if rank is not None else 999


def _rank_outcome(candidate_rank: int | None, full_rank: int | None) -> str:
    candidate_value = _rank_value(candidate_rank)
    full_value = _rank_value(full_rank)
    if candidate_value < full_value:
        return 'win'
    if candidate_value > full_value:
        return 'loss'
    return 'tie'


def _rank_delta(candidate_rank: int | None, baseline_rank: int | None) -> int | None:
    if candidate_rank is None or baseline_rank is None:
        return None
    return candidate_rank - baseline_rank


def _tradeoff_score(metrics: dict[str, Any]) -> float:
    return round(
        (
            metrics['top1_accuracy']
            + metrics['top3_accuracy']
            + metrics['precision_at_3']
            + metrics['mrr']
        )
        / 4,
        4,
    )


def _threshold_key(config: RankerConfig) -> str:
    return f'single_{config.min_single_chunk_score:.2f}_final_{config.min_final_score:.2f}'


def _aggregate_selective_metrics(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    overall = aggregate_metrics(case_results)
    covered = [case for case in case_results if case['coverage']]
    coverage = len(covered) / len(case_results)
    abstention_rate = 1 - coverage

    if covered:
        covered_top1 = mean(case['top1_hit'] for case in covered)
        covered_top3 = mean(case['top3_hit'] for case in covered)
        covered_mrr = mean(case['reciprocal_rank'] for case in covered)
    else:
        covered_top1 = 0.0
        covered_top3 = 0.0
        covered_mrr = 0.0

    return {
        'n_cases': len(case_results),
        'coverage': round(coverage, 4),
        'abstention_rate': round(abstention_rate, 4),
        'covered_case_top1_accuracy': round(covered_top1, 4),
        'covered_case_top3_accuracy': round(covered_top3, 4),
        'covered_case_mrr': round(covered_mrr, 4),
        'overall_top1_accuracy': overall['top1_accuracy'],
        'overall_top3_accuracy': overall['top3_accuracy'],
        'mean_recommended_count': overall['mean_recommended_count'],
    }


def _load_paraphrase_dataset(path: Path = PARAPHRASE_DATASET_PATH) -> list[ParaphraseCase]:
    if not path.exists():
        raise FileNotFoundError(f'Paraphrase dataset not found: {path}')

    rows: list[ParaphraseCase] = []
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_PARAPHRASE_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'Missing required paraphrase columns: {sorted(missing)}')

        for row in reader:
            if not any((value or '').strip() for value in row.values()):
                continue
            rows.append(
                ParaphraseCase(
                    source_test_id=(row['source_test_id'] or '').strip(),
                    paraphrase_id=(row['paraphrase_id'] or '').strip(),
                    paraphrase_level=(row['paraphrase_level'] or '').strip(),
                    sender_name=(row['sender_name'] or '').strip(),
                    sender_email=(row['sender_email'] or '').strip(),
                    outlet_name=(row['outlet_name'] or '').strip(),
                    subject=(row['subject'] or '').strip(),
                    body=(row['body'] or '').strip(),
                    expected_experts=parse_expected_experts(row['expected_experts'] or ''),
                )
            )
    return rows


def _paraphrase_to_eval_case(item: ParaphraseCase) -> EvalCase:
    return EvalCase(
        test_id=item.paraphrase_id,
        sender_name=item.sender_name,
        sender_email=item.sender_email,
        outlet_name=item.outlet_name,
        subject=item.subject,
        body=item.body,
        expected_experts=item.expected_experts,
    )


def _run_e1_ablation(
    dataset: list[EvalCase],
    baseline_metrics: dict[str, Any],
    *,
    output_paths: FocusedOutputPaths,
    dataset_path: Path,
    label: str,
) -> None:
    variant_results: dict[str, dict[str, Any]] = {}
    for key, spec in ABLATION_VARIANTS.items():
        case_results = evaluate_dataset(
            dataset,
            ranker_config=spec['config'],
            enquiry_id_prefix=f'e1-{key}',
        )
        metrics = aggregate_metrics(case_results)
        variant_results[key] = {
            'label': spec['label'],
            'config': ranker_config_to_dict(spec['config']),
            'metrics': metrics,
            'case_results': case_results,
            'tradeoff_score': _tradeoff_score(metrics),
        }

    full_case_lookup = {
        case['test_id']: case for case in variant_results[FULL_VARIANT_KEY]['case_results']
    }
    case_rows: list[dict[str, Any]] = []
    for key, variant in variant_results.items():
        outcome_counts = {'win': 0, 'loss': 0, 'tie': 0}
        for case in variant['case_results']:
            full_case = full_case_lookup[case['test_id']]
            outcome = _rank_outcome(case['first_relevant_rank'], full_case['first_relevant_rank'])
            outcome_counts[outcome] += 1
            case_rows.append(
                {
                    'variant_key': key,
                    'variant_label': variant['label'],
                    'test_id': case['test_id'],
                    'subject': case['subject'],
                    'predicted_experts': ' | '.join(case['predicted_experts']),
                    'first_relevant_rank': case['first_relevant_rank'],
                    'full_system_first_relevant_rank': full_case['first_relevant_rank'],
                    'rank_delta_vs_full_system': _rank_delta(
                        case['first_relevant_rank'],
                        full_case['first_relevant_rank'],
                    ),
                    'outcome_vs_full_system': outcome,
                    'top1_hit': case['top1_hit'],
                    'top3_hit': case['top3_hit'],
                    'top5_hit': case['top5_hit'],
                    'precision_at_3': case['precision_at_3'],
                    'reciprocal_rank': case['reciprocal_rank'],
                }
            )
        variant['versus_full_system'] = outcome_counts
        del variant['case_results']

    leader_key = max(
        variant_results,
        key=lambda variant_key: (
            variant_results[variant_key]['tradeoff_score'],
            variant_results[variant_key]['metrics']['top1_accuracy'],
        ),
    )

    summary = {
        'experiment': 'E1 Ablation',
        'label': label,
        'dataset': str(dataset_path),
        'baseline_reference': baseline_metrics,
        'tradeoff_method': 'Unweighted mean of Top-1, Top-3, Precision@3, and MRR.',
        'overall_tradeoff_leader': {
            'variant_key': leader_key,
            'variant_label': variant_results[leader_key]['label'],
            'tradeoff_score': variant_results[leader_key]['tradeoff_score'],
        },
        'full_system_is_tradeoff_leader': leader_key == FULL_VARIANT_KEY,
        'variants': variant_results,
    }

    output_paths.e1_summary.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding='utf-8',
    )
    _write_rows(output_paths.e1_cases, case_rows)


def _run_e2_selective_prediction(
    dataset: list[EvalCase],
    baseline_metrics: dict[str, Any],
    *,
    output_paths: FocusedOutputPaths,
    dataset_path: Path,
    label: str,
) -> None:
    setting_summaries: dict[str, dict[str, Any]] = {}
    case_rows: list[dict[str, Any]] = []

    for config in THRESHOLD_GRID:
        key = _threshold_key(config)
        case_results = evaluate_dataset(
            dataset,
            ranker_config=config,
            enquiry_id_prefix=f'e2-{key}',
        )
        summary = {
            'config': ranker_config_to_dict(config),
            'metrics': _aggregate_selective_metrics(case_results),
        }
        setting_summaries[key] = summary

        for case in case_results:
            case_rows.append(
                {
                    'setting_key': key,
                    'min_single_chunk_score': config.min_single_chunk_score,
                    'min_final_score': config.min_final_score,
                    'test_id': case['test_id'],
                    'subject': case['subject'],
                    'coverage': case['coverage'],
                    'abstained': int(not case['coverage']),
                    'first_relevant_rank': case['first_relevant_rank'],
                    'top1_hit': case['top1_hit'],
                    'top3_hit': case['top3_hit'],
                    'reciprocal_rank': case['reciprocal_rank'],
                    'recommended_count': case['recommended_count'],
                    'predicted_experts': ' | '.join(case['predicted_experts']),
                }
            )

    baseline_selective = setting_summaries[DEFAULT_THRESHOLD_KEY]['metrics']
    tradeoff_candidates = []
    for key, summary in setting_summaries.items():
        metrics = summary['metrics']
        if key == DEFAULT_THRESHOLD_KEY:
            continue
        if metrics['coverage'] < baseline_selective['coverage'] and (
            metrics['covered_case_top1_accuracy'] > baseline_selective['covered_case_top1_accuracy']
            or metrics['covered_case_mrr'] > baseline_selective['covered_case_mrr']
        ):
            tradeoff_candidates.append({'setting_key': key, 'metrics': metrics})

    summary = {
        'experiment': 'E2 Selective Prediction / Abstention',
        'label': label,
        'dataset': str(dataset_path),
        'baseline_reference': baseline_metrics,
        'default_setting_key': DEFAULT_THRESHOLD_KEY,
        'definitions': {
            'coverage': 'Proportion of cases with at least one returned recommendation after thresholding.',
            'abstention': 'A case with zero returned recommendations after thresholding.',
        },
        'settings': setting_summaries,
        'tradeoff_candidates': tradeoff_candidates,
    }

    output_paths.e2_summary.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding='utf-8',
    )
    _write_rows(output_paths.e2_cases, case_rows)


def _run_e5_paraphrase(
    dataset: list[EvalCase],
    baseline_metrics: dict[str, Any],
    *,
    output_paths: FocusedOutputPaths,
    dataset_path: Path,
    paraphrase_path: Path,
    label: str,
) -> None:
    paraphrases = _load_paraphrase_dataset(paraphrase_path)
    source_ids: list[str] = []
    for item in paraphrases:
        if item.source_test_id not in source_ids:
            source_ids.append(item.source_test_id)

    source_cases = select_cases(dataset, source_ids)
    source_case_lookup = {case.test_id: case for case in source_cases}
    source_results = {
        case['test_id']: case
        for case in evaluate_dataset(source_cases, enquiry_id_prefix='e5-source')
    }

    case_rows: list[dict[str, Any]] = []
    top3_jaccards: list[float] = []
    rank_deltas: list[int] = []
    abs_rank_deltas: list[int] = []
    mrr_deltas: list[float] = []
    topic_drift_count = 0

    for item in paraphrases:
        eval_case = _paraphrase_to_eval_case(item)
        paraphrase_result = evaluate_case(eval_case, enquiry_id_prefix='e5-paraphrase')
        source_result = source_results[item.source_test_id]
        jaccard_score = jaccard_at_k(source_result['predicted_experts'], paraphrase_result['predicted_experts'])
        rank_delta = _rank_delta(paraphrase_result['first_relevant_rank'], source_result['first_relevant_rank'])
        mrr_delta = round(paraphrase_result['reciprocal_rank'] - source_result['reciprocal_rank'], 4)
        source_topics = source_result.get('topic_labels', [])
        paraphrase_topics = paraphrase_result.get('topic_labels', [])
        drift_terms = sorted(set(source_topics) ^ set(paraphrase_topics))

        top3_jaccards.append(jaccard_score)
        mrr_deltas.append(mrr_delta)
        if rank_delta is not None:
            rank_deltas.append(rank_delta)
            abs_rank_deltas.append(abs(rank_delta))
        if drift_terms:
            topic_drift_count += 1

        case_rows.append(
            {
                'source_test_id': item.source_test_id,
                'paraphrase_id': item.paraphrase_id,
                'paraphrase_level': item.paraphrase_level,
                'source_subject': source_case_lookup[item.source_test_id].subject,
                'paraphrase_subject': item.subject,
                'source_predicted_experts': ' | '.join(source_result['predicted_experts']),
                'paraphrase_predicted_experts': ' | '.join(paraphrase_result['predicted_experts']),
                'top3_jaccard': round(jaccard_score, 4),
                'source_first_relevant_rank': source_result['first_relevant_rank'],
                'paraphrase_first_relevant_rank': paraphrase_result['first_relevant_rank'],
                'first_relevant_rank_delta': rank_delta,
                'source_mrr': source_result['reciprocal_rank'],
                'paraphrase_mrr': paraphrase_result['reciprocal_rank'],
                'mrr_delta': mrr_delta,
                'source_topic_labels': ' | '.join(source_topics),
                'paraphrase_topic_labels': ' | '.join(paraphrase_topics),
                'topic_label_drift': ' | '.join(drift_terms),
            }
        )

    summary = {
        'experiment': 'E5 Robustness to Paraphrase',
        'label': label,
        'dataset': str(dataset_path),
        'paraphrase_dataset': str(paraphrase_path),
        'baseline_reference': baseline_metrics,
        'n_source_cases': len(source_ids),
        'n_paraphrases': len(paraphrases),
        'metrics': {
            'mean_top3_jaccard': round(mean(top3_jaccards), 4) if top3_jaccards else 0.0,
            'exact_top3_match_rate': round(mean(1 if score == 1.0 else 0 for score in top3_jaccards), 4) if top3_jaccards else 0.0,
            'mean_first_relevant_rank_delta': round(mean(rank_deltas), 4) if rank_deltas else None,
            'mean_absolute_first_relevant_rank_delta': round(mean(abs_rank_deltas), 4) if abs_rank_deltas else None,
            'mean_mrr_delta': round(mean(mrr_deltas), 4) if mrr_deltas else 0.0,
            'topic_label_drift_rate': round(topic_drift_count / len(paraphrases), 4) if paraphrases else 0.0,
        },
    }

    output_paths.e5_summary.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False, default=str),
        encoding='utf-8',
    )
    _write_rows(output_paths.e5_cases, case_rows)


def main() -> None:
    args = parse_args()
    output_paths = _build_output_paths(args.output_dir)
    output_paths.output_dir.mkdir(parents=True, exist_ok=True)

    dataset = load_dataset(args.dataset_path)
    if args.baseline_results_path.exists():
        baseline_payload = json.loads(args.baseline_results_path.read_text(encoding='utf-8'))
        baseline_metrics = baseline_payload['metrics']
    else:
        baseline_metrics = aggregate_metrics(evaluate_dataset(dataset, enquiry_id_prefix='focused-baseline'))

    baseline_reference = {
        'label': args.label,
        'dataset': str(args.dataset_path),
        'paraphrase_dataset': str(args.paraphrase_path),
        'fixed_corpus_policy': 'Focused evaluation uses the current processed profiles and embeddings without regeneration.',
        'metrics': baseline_metrics,
    }
    output_paths.baseline_reference.write_text(
        json.dumps(baseline_reference, indent=2, ensure_ascii=False, default=str),
        encoding='utf-8',
    )

    _run_e1_ablation(dataset, baseline_metrics, output_paths=output_paths, dataset_path=args.dataset_path, label=args.label)
    _run_e2_selective_prediction(dataset, baseline_metrics, output_paths=output_paths, dataset_path=args.dataset_path, label=args.label)
    _run_e5_paraphrase(
        dataset,
        baseline_metrics,
        output_paths=output_paths,
        dataset_path=args.dataset_path,
        paraphrase_path=args.paraphrase_path,
        label=args.label,
    )

    print(f'Saved focused evaluation outputs to: {output_paths.output_dir}')


if __name__ == '__main__':
    main()

