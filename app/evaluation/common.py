from __future__ import annotations

import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from app.enquiry.processor import process_enquiry
from app.retrieval.expert_ranker import RankerConfig


BENCHMARK_DIR = Path('data/evaluation/benchmarks')
ORIGINAL_DATASET_PATH = BENCHMARK_DIR / 'gold_test_set_100_original.csv'
CLEANED_DATASET_PATH = BENCHMARK_DIR / 'gold_test_set_100_cleaned.csv'
ABSTENTION_DATASET_PATH = BENCHMARK_DIR / 'gold_test_set_abstention.csv'
DATASET_PATH = CLEANED_DATASET_PATH
OUTPUT_DIR = Path('data/evaluation')


@dataclass(frozen=True)
class EvalCase:
    test_id: str
    sender_name: str
    sender_email: str
    outlet_name: str
    subject: str
    body: str
    expected_experts: list[str]


REQUIRED_COLUMNS = {
    'test_id',
    'sender_name',
    'sender_email',
    'outlet_name',
    'subject',
    'body',
    'expected_experts',
}


def normalize_name(name: str) -> str:
    return ' '.join(name.strip().lower().split())


def parse_expected_experts(raw: str) -> list[str]:
    if not raw:
        return []
    return [normalize_name(item) for item in raw.split('|') if item.strip()]


def load_dataset(path: Path = DATASET_PATH) -> list[EvalCase]:
    if not path.exists():
        raise FileNotFoundError(f'Dataset not found: {path}')

    rows: list[EvalCase] = []
    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'Missing required columns: {sorted(missing)}')

        for row in reader:
            if not any((value or '').strip() for value in row.values()):
                continue
            rows.append(
                EvalCase(
                    test_id=(row['test_id'] or '').strip(),
                    sender_name=(row['sender_name'] or '').strip(),
                    sender_email=(row['sender_email'] or '').strip(),
                    outlet_name=(row['outlet_name'] or '').strip(),
                    subject=(row['subject'] or '').strip(),
                    body=(row['body'] or '').strip(),
                    expected_experts=parse_expected_experts(row['expected_experts'] or ''),
                )
            )
    return rows


def dataset_lookup(cases: Iterable[EvalCase]) -> dict[str, EvalCase]:
    return {case.test_id: case for case in cases}


def select_cases(cases: Iterable[EvalCase], test_ids: list[str]) -> list[EvalCase]:
    lookup = dataset_lookup(cases)
    missing = [test_id for test_id in test_ids if test_id not in lookup]
    if missing:
        raise ValueError(f'Unknown test IDs requested: {missing}')
    return [lookup[test_id] for test_id in test_ids]


def first_relevant_rank(predicted_names: list[str], expected_names: set[str]) -> int | None:
    for index, name in enumerate(predicted_names, start=1):
        if normalize_name(name) in expected_names:
            return index
    return None


def precision_at_k(predicted_names: list[str], expected_names: set[str], k: int) -> float:
    top_k = predicted_names[:k]
    if not top_k:
        return 0.0
    relevant = sum(1 for name in top_k if normalize_name(name) in expected_names)
    return relevant / k


def hit_at_k(predicted_names: list[str], expected_names: set[str], k: int) -> int:
    return int(any(normalize_name(name) in expected_names for name in predicted_names[:k]))


def jaccard_at_k(left: list[str], right: list[str], k: int = 3) -> float:
    left_set = {normalize_name(name) for name in left[:k]}
    right_set = {normalize_name(name) for name in right[:k]}
    if not left_set and not right_set:
        return 1.0
    union = left_set | right_set
    if not union:
        return 0.0
    return len(left_set & right_set) / len(union)


def safe_bool_to_int(value: bool) -> int:
    return 1 if value else 0


def evaluate_case(
    case: EvalCase,
    *,
    ranker_config: RankerConfig | None = None,
    enquiry_id_prefix: str = 'eval',
) -> dict[str, Any]:
    result = process_enquiry(
        sender_name=case.sender_name,
        sender_email=case.sender_email,
        outlet_name=case.outlet_name or None,
        subject=case.subject,
        body=case.body,
        enquiry_id=f'{enquiry_id_prefix}-{case.test_id}',
        persist_audit=False,
        ranker_config=ranker_config,
    )

    recommendations = result.get('recommended_experts', [])
    predicted_names = [expert['name'] for expert in recommendations]
    expected_names = set(case.expected_experts)

    rank = first_relevant_rank(predicted_names, expected_names)
    top1 = hit_at_k(predicted_names, expected_names, 1)
    top3 = hit_at_k(predicted_names, expected_names, 3)
    top5 = hit_at_k(predicted_names, expected_names, 5)
    p_at_3 = precision_at_k(predicted_names, expected_names, 3)
    reciprocal_rank = 0.0 if rank is None else 1.0 / rank
    coverage = int(bool(predicted_names))
    approval_proxy = top3
    supporting_chunk_count = sum(len(expert.get('supporting_chunks', [])) for expert in recommendations)

    return {
        'test_id': case.test_id,
        'subject': case.subject,
        'expected_experts': case.expected_experts,
        'predicted_experts': predicted_names,
        'top1_hit': top1,
        'top3_hit': top3,
        'top5_hit': top5,
        'precision_at_3': round(p_at_3, 4),
        'reciprocal_rank': round(reciprocal_rank, 4),
        'coverage': coverage,
        'approval_proxy': approval_proxy,
        'first_relevant_rank': rank,
        'recommended_count': len(predicted_names),
        'supporting_chunk_count': supporting_chunk_count,
        'verification': result.get('verification', {}),
        'topic_labels': result.get('topic_labels', []),
        'staff_summary': result.get('staff_summary'),
        'raw_result': {
            'enquiry_id': result.get('enquiry_id'),
            'created_at': str(result.get('created_at')),
            'verification': result.get('verification'),
            'topic_labels': result.get('topic_labels'),
            'staff_summary': result.get('staff_summary'),
        },
    }


def evaluate_dataset(
    cases: list[EvalCase],
    *,
    ranker_config: RankerConfig | None = None,
    enquiry_id_prefix: str = 'eval',
) -> list[dict[str, Any]]:
    return [
        evaluate_case(case, ranker_config=ranker_config, enquiry_id_prefix=enquiry_id_prefix)
        for case in cases
    ]


def aggregate_metrics(case_results: list[dict[str, Any]]) -> dict[str, Any]:
    if not case_results:
        raise ValueError('No case results to aggregate')

    recommendation_counter: Counter[str] = Counter()
    for case in case_results:
        for name in case['predicted_experts']:
            recommendation_counter[name] += 1

    top1_accuracy = mean(case['top1_hit'] for case in case_results)
    top3_accuracy = mean(case['top3_hit'] for case in case_results)
    top5_accuracy = mean(case['top5_hit'] for case in case_results)
    precision3 = mean(case['precision_at_3'] for case in case_results)
    mrr = mean(case['reciprocal_rank'] for case in case_results)
    coverage = mean(case['coverage'] for case in case_results)
    approval_proxy_rate = mean(case['approval_proxy'] for case in case_results)
    mean_recommended_count = mean(case['recommended_count'] for case in case_results)
    mean_supporting_chunk_count = mean(case['supporting_chunk_count'] for case in case_results)

    recognised_outlet_rate = mean(
        safe_bool_to_int(case['verification'].get('recognised_outlet', False))
        for case in case_results
    )
    manual_review_rate = mean(
        safe_bool_to_int(case['verification'].get('manual_review_required', False))
        for case in case_results
    )

    concentration = recommendation_counter.most_common(10)

    return {
        'n_cases': len(case_results),
        'top1_accuracy': round(top1_accuracy, 4),
        'top3_accuracy': round(top3_accuracy, 4),
        'top5_accuracy': round(top5_accuracy, 4),
        'precision_at_3': round(precision3, 4),
        'mrr': round(mrr, 4),
        'coverage': round(coverage, 4),
        'approval_proxy_rate': round(approval_proxy_rate, 4),
        'mean_recommended_count': round(mean_recommended_count, 4),
        'mean_supporting_chunk_count': round(mean_supporting_chunk_count, 4),
        'recognised_outlet_rate': round(recognised_outlet_rate, 4),
        'manual_review_rate': round(manual_review_rate, 4),
        'recommendation_concentration_top10': [
            {'expert': name, 'count': count} for name, count in concentration
        ],
    }


def write_detailed_csv(case_results: list[dict[str, Any]], path: Path) -> None:
    rows = []
    for case in case_results:
        rows.append(
            {
                'test_id': case['test_id'],
                'subject': case['subject'],
                'expected_experts': ' | '.join(case['expected_experts']),
                'predicted_experts': ' | '.join(case['predicted_experts']),
                'top1_hit': case['top1_hit'],
                'top3_hit': case['top3_hit'],
                'top5_hit': case['top5_hit'],
                'precision_at_3': case['precision_at_3'],
                'reciprocal_rank': case['reciprocal_rank'],
                'coverage': case['coverage'],
                'approval_proxy': case['approval_proxy'],
                'first_relevant_rank': case['first_relevant_rank'],
                'recommended_count': case['recommended_count'],
                'supporting_chunk_count': case['supporting_chunk_count'],
                'recognised_outlet': case['verification'].get('recognised_outlet', False),
                'manual_review_required': case['verification'].get('manual_review_required', False),
                'topic_labels': ' | '.join(case['topic_labels']),
            }
        )

    if not rows:
        raise ValueError('No case rows available to write')

    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def build_output(case_results: list[dict[str, Any]], *, dataset_path: Path, label: str) -> dict[str, Any]:
    return {
        'label': label,
        'dataset': str(dataset_path),
        'metrics': aggregate_metrics(case_results),
        'cases': case_results,
    }
