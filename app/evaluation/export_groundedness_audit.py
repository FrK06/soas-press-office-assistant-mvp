from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from app.evaluation.common import DATASET_PATH, load_dataset, select_cases
from app.enquiry.processor import process_enquiry


GROUND_TRUTH_MANIFEST = Path('data/evaluation/groundedness_audit_cases.csv')
FOCUSED_OUTPUT_DIR = Path('data/evaluation/focused')
ANNOTATION_SHEET_NAME = 'e4_groundedness_annotation_sheet.csv'
RESULTS_NAME = 'e4_groundedness_results.json'
REQUIRED_MANIFEST_COLUMNS = {'test_id'}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Export the groundedness annotation sheet.')
    parser.add_argument('--dataset-path', type=Path, default=DATASET_PATH)
    parser.add_argument('--manifest-path', type=Path, default=GROUND_TRUTH_MANIFEST)
    parser.add_argument('--output-dir', type=Path, default=FOCUSED_OUTPUT_DIR)
    parser.add_argument('--label', default='cleaned_default')
    return parser.parse_args()


def _load_manifest(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f'Groundedness manifest not found: {path}')

    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_MANIFEST_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'Missing required manifest columns: {sorted(missing)}')
        test_ids = [(row['test_id'] or '').strip() for row in reader if (row['test_id'] or '').strip()]

    if not test_ids:
        raise ValueError('Groundedness manifest is empty')
    return test_ids


def _chunk_value(expert: dict, index: int, field: str) -> str:
    chunks = expert.get('supporting_chunks', [])
    if index >= len(chunks):
        return ''
    return str(chunks[index].get(field, '') or '')


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    annotation_sheet_path = output_dir / ANNOTATION_SHEET_NAME
    results_path = output_dir / RESULTS_NAME

    output_dir.mkdir(parents=True, exist_ok=True)
    test_ids = _load_manifest(args.manifest_path)
    dataset = load_dataset(args.dataset_path)
    audit_cases = select_cases(dataset, test_ids)

    rows = []
    for case in audit_cases:
        result = process_enquiry(
            sender_name=case.sender_name,
            sender_email=case.sender_email,
            outlet_name=case.outlet_name or None,
            subject=case.subject,
            body=case.body,
            enquiry_id=f'e4-{case.test_id}',
            persist_audit=False,
        )

        for rank, expert in enumerate(result.get('recommended_experts', [])[:3], start=1):
            rows.append(
                {
                    'test_id': case.test_id,
                    'recommendation_rank': rank,
                    'sender_email': case.sender_email,
                    'outlet_name': case.outlet_name,
                    'subject': case.subject,
                    'body': case.body,
                    'topic_labels': ' | '.join(result.get('topic_labels', [])),
                    'expert_name': expert.get('name', ''),
                    'expert_title': expert.get('title', ''),
                    'expert_department': expert.get('department', ''),
                    'confidence': expert.get('confidence', ''),
                    'rationale': expert.get('rationale', ''),
                    'supporting_chunk_1_section': _chunk_value(expert, 0, 'section'),
                    'supporting_chunk_1_text': _chunk_value(expert, 0, 'text'),
                    'supporting_chunk_2_section': _chunk_value(expert, 1, 'section'),
                    'supporting_chunk_2_text': _chunk_value(expert, 1, 'text'),
                    'supporting_chunk_3_section': _chunk_value(expert, 2, 'section'),
                    'supporting_chunk_3_text': _chunk_value(expert, 2, 'text'),
                    'annotation_label': '',
                    'annotation_note': '',
                }
            )

    if not rows:
        raise ValueError('No groundedness audit rows were generated.')

    with annotation_sheet_path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    placeholder = {
        'experiment': 'E4 Groundedness / Evidence Support',
        'status': 'pending_manual_annotation',
        'label': args.label,
        'dataset': str(args.dataset_path),
        'annotation_sheet': str(annotation_sheet_path),
        'manifest': str(args.manifest_path),
        'next_step': 'Complete annotation_label values as Supported, Partially Supported, or Unsupported, then run python -m app.evaluation.score_groundedness.',
    }
    results_path.write_text(json.dumps(placeholder, indent=2, ensure_ascii=False), encoding='utf-8')

    print(f'Saved annotation sheet to: {annotation_sheet_path}')
    print(f'Saved placeholder results to: {results_path}')


if __name__ == '__main__':
    main()
