from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean


GROUND_TRUTH_MANIFEST = Path('data/evaluation/groundedness_audit_cases.csv')
ANNOTATION_SHEET_PATH = Path('data/evaluation/focused/e4_groundedness_annotation_sheet.csv')
RESULTS_PATH = Path('data/evaluation/focused/e4_groundedness_results.json')
VALID_LABELS = {'Supported', 'Partially Supported', 'Unsupported'}
REQUIRED_COLUMNS = {
    'test_id',
    'recommendation_rank',
    'sender_email',
    'outlet_name',
    'subject',
    'body',
    'topic_labels',
    'expert_name',
    'expert_title',
    'expert_department',
    'confidence',
    'rationale',
    'supporting_chunk_1_section',
    'supporting_chunk_1_text',
    'supporting_chunk_2_section',
    'supporting_chunk_2_text',
    'supporting_chunk_3_section',
    'supporting_chunk_3_text',
    'annotation_label',
    'annotation_note',
}


def _load_manifest(path: Path = GROUND_TRUTH_MANIFEST) -> list[str]:
    with path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        return [(row['test_id'] or '').strip() for row in reader if (row['test_id'] or '').strip()]


def _load_annotations(path: Path = ANNOTATION_SHEET_PATH) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f'Annotation sheet not found: {path}')

    with path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'Missing required annotation columns: {sorted(missing)}')
        rows = [row for row in reader if any((value or '').strip() for value in row.values())]

    if not rows:
        raise ValueError('Annotation sheet is empty')
    return rows


def _validate_annotations(rows: list[dict[str, str]], manifest_ids: list[str]) -> None:
    row_keys = set()
    test_ids_in_rows = set()
    ranks_by_case: dict[str, set[str]] = defaultdict(set)

    for row in rows:
        test_id = (row['test_id'] or '').strip()
        label = (row['annotation_label'] or '').strip()
        rank = (row['recommendation_rank'] or '').strip()

        if not test_id:
            raise ValueError('Annotation row is missing test_id')
        if not rank:
            raise ValueError(f'Annotation row for {test_id} is missing recommendation_rank')
        if rank not in {'1', '2', '3'}:
            raise ValueError(f'Annotation row for {test_id} has invalid recommendation_rank: {rank}')
        if not label:
            raise ValueError(f'Annotation row for {test_id} rank {rank} is missing annotation_label')
        if label not in VALID_LABELS:
            raise ValueError(f'Annotation row for {test_id} rank {rank} has invalid annotation_label: {label}')

        key = (test_id, rank)
        if key in row_keys:
            raise ValueError(f'Duplicate annotation row detected for {test_id} rank {rank}')
        row_keys.add(key)

        test_ids_in_rows.add(test_id)
        ranks_by_case[test_id].add(rank)

    missing_cases = [test_id for test_id in manifest_ids if test_id not in test_ids_in_rows]
    if missing_cases:
        raise ValueError(f'Missing annotated cases from manifest: {missing_cases}')

    missing_top1 = [test_id for test_id in manifest_ids if '1' not in ranks_by_case[test_id]]
    if missing_top1:
        raise ValueError(f'Missing top-rank annotations for cases: {missing_top1}')


def main() -> None:
    manifest_ids = _load_manifest(GROUND_TRUTH_MANIFEST)
    rows = _load_annotations(ANNOTATION_SHEET_PATH)
    _validate_annotations(rows, manifest_ids)

    top1_rows = [row for row in rows if row['recommendation_rank'] == '1']
    top3_rows = [row for row in rows if row['recommendation_rank'] in {'1', '2', '3'}]
    label_counts = Counter(row['annotation_label'] for row in top3_rows)

    results = {
        'experiment': 'E4 Groundedness / Evidence Support',
        'status': 'completed',
        'annotation_sheet': str(ANNOTATION_SHEET_PATH),
        'manifest': str(GROUND_TRUTH_MANIFEST),
        'n_cases': len(manifest_ids),
        'n_top1_annotations': len(top1_rows),
        'n_top3_annotations': len(top3_rows),
        'primary_metrics': {
            'supported_at_1': round(mean(1 if row['annotation_label'] == 'Supported' else 0 for row in top1_rows), 4),
            'supported_at_3': round(mean(1 if row['annotation_label'] == 'Supported' else 0 for row in top3_rows), 4),
        },
        'secondary_metrics': {
            'supported_or_partially_supported_at_3': round(
                mean(1 if row['annotation_label'] in {'Supported', 'Partially Supported'} else 0 for row in top3_rows),
                4,
            ),
        },
        'error_metrics': {
            'unsupported_rate': round(mean(1 if row['annotation_label'] == 'Unsupported' else 0 for row in top3_rows), 4),
        },
        'label_counts': {
            'Supported': label_counts.get('Supported', 0),
            'Partially Supported': label_counts.get('Partially Supported', 0),
            'Unsupported': label_counts.get('Unsupported', 0),
        },
    }

    RESULTS_PATH.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )
    print(f'Saved groundedness results to: {RESULTS_PATH}')


if __name__ == '__main__':
    main()

