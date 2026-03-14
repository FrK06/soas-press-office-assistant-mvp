import csv
import json

from app.evaluation.common import EvalCase
from app.evaluation.run_focused_eval import (
    ABLATION_VARIANTS,
    FULL_VARIANT_KEY,
    ParaphraseCase,
    _aggregate_selective_metrics,
    _run_e5_paraphrase,
)
from app.evaluation import score_groundedness


def test_ablation_variants_match_plan() -> None:
    assert list(ABLATION_VARIANTS.keys()) == [
        'variant_a_retrieval_only',
        'variant_b_topic_boosts',
        'variant_c_topic_and_media',
        'variant_d_full_system',
    ]
    assert FULL_VARIANT_KEY == 'variant_d_full_system'
    assert ABLATION_VARIANTS['variant_a_retrieval_only']['config'].enable_topic_boosts is False
    assert ABLATION_VARIANTS['variant_a_retrieval_only']['config'].enable_media_signal_boost is False
    assert ABLATION_VARIANTS['variant_a_retrieval_only']['config'].enable_diversity_penalty is False
    assert ABLATION_VARIANTS['variant_b_topic_boosts']['config'].enable_topic_boosts is True
    assert ABLATION_VARIANTS['variant_b_topic_boosts']['config'].enable_media_signal_boost is False
    assert ABLATION_VARIANTS['variant_c_topic_and_media']['config'].enable_media_signal_boost is True
    assert ABLATION_VARIANTS['variant_d_full_system']['config'].enable_diversity_penalty is True



def test_selective_metrics_define_coverage_and_abstention() -> None:
    case_results = [
        {
            'coverage': 1,
            'top1_hit': 1,
            'top3_hit': 1,
            'reciprocal_rank': 1.0,
            'recommended_count': 2,
            'top5_hit': 1,
            'precision_at_3': 0.6667,
            'approval_proxy': 1,
            'supporting_chunk_count': 3,
            'predicted_experts': ['A', 'B'],
            'verification': {'recognised_outlet': True, 'manual_review_required': False},
        },
        {
            'coverage': 0,
            'top1_hit': 0,
            'top3_hit': 0,
            'reciprocal_rank': 0.0,
            'recommended_count': 0,
            'top5_hit': 0,
            'precision_at_3': 0.0,
            'approval_proxy': 0,
            'supporting_chunk_count': 0,
            'predicted_experts': [],
            'verification': {'recognised_outlet': False, 'manual_review_required': True},
        },
    ]

    metrics = _aggregate_selective_metrics(case_results)

    assert metrics['coverage'] == 0.5
    assert metrics['abstention_rate'] == 0.5
    assert metrics['covered_case_top1_accuracy'] == 1.0
    assert metrics['covered_case_top3_accuracy'] == 1.0
    assert metrics['covered_case_mrr'] == 1.0
    assert metrics['overall_top1_accuracy'] == 0.5
    assert metrics['mean_recommended_count'] == 1



def test_groundedness_scorer_computes_strict_relaxed_and_error_metrics(tmp_path, monkeypatch) -> None:
    manifest_path = tmp_path / 'groundedness_cases.csv'
    annotation_path = tmp_path / 'annotation_sheet.csv'
    results_path = tmp_path / 'groundedness_results.json'

    manifest_path.write_text('test_id\nT001\nT002\n', encoding='utf-8')
    annotation_rows = [
        {
            'test_id': 'T001',
            'recommendation_rank': '1',
            'sender_email': 'reporter1@example.com',
            'outlet_name': 'Outlet A',
            'subject': 'Subject A',
            'body': 'Body A',
            'topic_labels': 'Migration',
            'expert_name': 'Expert A',
            'expert_title': 'Title A',
            'expert_department': 'Dept A',
            'confidence': 'High',
            'rationale': 'Reason A',
            'supporting_chunk_1_section': 'bio',
            'supporting_chunk_1_text': 'Chunk 1',
            'supporting_chunk_2_section': '',
            'supporting_chunk_2_text': '',
            'supporting_chunk_3_section': '',
            'supporting_chunk_3_text': '',
            'annotation_label': 'Supported',
            'annotation_note': '',
        },
        {
            'test_id': 'T001',
            'recommendation_rank': '2',
            'sender_email': 'reporter1@example.com',
            'outlet_name': 'Outlet A',
            'subject': 'Subject A',
            'body': 'Body A',
            'topic_labels': 'Migration',
            'expert_name': 'Expert B',
            'expert_title': 'Title B',
            'expert_department': 'Dept B',
            'confidence': 'Medium',
            'rationale': 'Reason B',
            'supporting_chunk_1_section': 'research',
            'supporting_chunk_1_text': 'Chunk 2',
            'supporting_chunk_2_section': '',
            'supporting_chunk_2_text': '',
            'supporting_chunk_3_section': '',
            'supporting_chunk_3_text': '',
            'annotation_label': 'Partially Supported',
            'annotation_note': 'Broad but relevant.',
        },
        {
            'test_id': 'T002',
            'recommendation_rank': '1',
            'sender_email': 'reporter2@example.com',
            'outlet_name': 'Outlet B',
            'subject': 'Subject B',
            'body': 'Body B',
            'topic_labels': 'Politics',
            'expert_name': 'Expert C',
            'expert_title': 'Title C',
            'expert_department': 'Dept C',
            'confidence': 'Low',
            'rationale': 'Reason C',
            'supporting_chunk_1_section': 'bio',
            'supporting_chunk_1_text': 'Chunk 3',
            'supporting_chunk_2_section': '',
            'supporting_chunk_2_text': '',
            'supporting_chunk_3_section': '',
            'supporting_chunk_3_text': '',
            'annotation_label': 'Unsupported',
            'annotation_note': 'Not grounded enough.',
        },
        {
            'test_id': 'T002',
            'recommendation_rank': '2',
            'sender_email': 'reporter2@example.com',
            'outlet_name': 'Outlet B',
            'subject': 'Subject B',
            'body': 'Body B',
            'topic_labels': 'Politics',
            'expert_name': 'Expert D',
            'expert_title': 'Title D',
            'expert_department': 'Dept D',
            'confidence': 'Medium',
            'rationale': 'Reason D',
            'supporting_chunk_1_section': 'research',
            'supporting_chunk_1_text': 'Chunk 4',
            'supporting_chunk_2_section': '',
            'supporting_chunk_2_text': '',
            'supporting_chunk_3_section': '',
            'supporting_chunk_3_text': '',
            'annotation_label': 'Supported',
            'annotation_note': '',
        },
    ]
    with annotation_path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(annotation_rows[0].keys()))
        writer.writeheader()
        writer.writerows(annotation_rows)

    monkeypatch.setattr(score_groundedness, 'GROUND_TRUTH_MANIFEST', manifest_path)
    monkeypatch.setattr(score_groundedness, 'ANNOTATION_SHEET_PATH', annotation_path)
    monkeypatch.setattr(score_groundedness, 'RESULTS_PATH', results_path)

    score_groundedness.main()

    results = json.loads(results_path.read_text(encoding='utf-8'))
    assert results['primary_metrics']['supported_at_1'] == 0.5
    assert results['primary_metrics']['supported_at_3'] == 0.5
    assert results['secondary_metrics']['supported_or_partially_supported_at_3'] == 0.75
    assert results['error_metrics']['unsupported_rate'] == 0.25



def test_paraphrase_runner_pairs_paraphrases_with_source_cases(tmp_path, monkeypatch) -> None:
    dataset = [
        EvalCase(
            test_id='T001',
            sender_name='Reporter',
            sender_email='reporter@example.com',
            outlet_name='Outlet',
            subject='Source subject',
            body='Source body',
            expected_experts=['expert a'],
        )
    ]
    paraphrase_case = ParaphraseCase(
        source_test_id='T001',
        paraphrase_id='T001-N',
        paraphrase_level='near',
        sender_name='Reporter',
        sender_email='reporter@example.com',
        outlet_name='Outlet',
        subject='Paraphrase subject',
        body='Paraphrase body',
        expected_experts=['expert a'],
    )

    summary_path = tmp_path / 'e5_summary.json'
    cases_path = tmp_path / 'e5_cases.csv'
    monkeypatch.setattr('app.evaluation.run_focused_eval.E5_SUMMARY_JSON', summary_path)
    monkeypatch.setattr('app.evaluation.run_focused_eval.E5_CASES_CSV', cases_path)
    monkeypatch.setattr('app.evaluation.run_focused_eval._load_paraphrase_dataset', lambda: [paraphrase_case])

    def fake_evaluate_dataset(cases, ranker_config=None, enquiry_id_prefix='eval'):
        assert len(cases) == 1
        return [
            {
                'test_id': 'T001',
                'subject': 'Source subject',
                'predicted_experts': ['Expert A', 'Expert B'],
                'first_relevant_rank': 1,
                'reciprocal_rank': 1.0,
                'topic_labels': ['Migration'],
            }
        ]

    def fake_evaluate_case(case, ranker_config=None, enquiry_id_prefix='eval'):
        assert case.test_id == 'T001-N'
        return {
            'test_id': 'T001-N',
            'subject': 'Paraphrase subject',
            'predicted_experts': ['Expert A', 'Expert C'],
            'first_relevant_rank': 1,
            'reciprocal_rank': 1.0,
            'topic_labels': ['Migration'],
        }

    monkeypatch.setattr('app.evaluation.run_focused_eval.evaluate_dataset', fake_evaluate_dataset)
    monkeypatch.setattr('app.evaluation.run_focused_eval.evaluate_case', fake_evaluate_case)

    _run_e5_paraphrase(dataset, baseline_metrics={'top1_accuracy': 0.62})

    rows = list(csv.DictReader(cases_path.open(encoding='utf-8')))
    summary = json.loads(summary_path.read_text(encoding='utf-8'))

    assert len(rows) == 1
    assert rows[0]['source_test_id'] == 'T001'
    assert float(rows[0]['top3_jaccard']) == 0.3333
    assert summary['metrics']['mean_top3_jaccard'] == 0.3333
    assert summary['metrics']['mean_mrr_delta'] == 0.0
