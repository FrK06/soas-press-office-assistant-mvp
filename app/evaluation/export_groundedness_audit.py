from __future__ import annotations

import csv
import json
from pathlib import Path

from app.evaluation.common import DATASET_PATH, load_dataset, select_cases
from app.enquiry.processor import process_enquiry


GROUND_TRUTH_MANIFEST = Path('data/evaluation/groundedness_audit_cases.csv')
FOCUSED_OUTPUT_DIR = Path('data/evaluation/focused')
ANNOTATION_SHEET_PATH = FOCUSED_OUTPUT_DIR / 'e4_groundedness_annotation_sheet.csv'
RESULTS_PATH = FOCUSED_OUTPUT_DIR / 'e4_groundedness_results.json'


REQUIRED_MANIFEST_COLUMNS = {'test_id'}


def _load_manifest(path: Path = GROUND_TRUTH_MANIFEST) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f'Groundedness manifest not found: {path}')

    with path.open('r', encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
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
    FOCUSED_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    test_ids = _load_manifest(GROUND_TRUTH_MANIFEST)
    dataset = load_dataset(DATASET_PATH)
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

    with ANNOTATION_SHEET_PATH.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    placeholder = {
        'experiment': 'E4 Groundedness / Evidence Support',
        'status': 'pending_manual_annotation',
        'annotation_sheet': str(ANNOTATION_SHEET_PATH),
        'manifest': str(GROUND_TRUTH_MANIFEST),
        'next_step': 'Complete annotation_label values as Supported, Partially Supported, or Unsupported, then run python -m app.evaluation.score_groundedness.',
    }
    RESULTS_PATH.write_text(
        json.dumps(placeholder, indent=2, ensure_ascii=False),
        encoding='utf-8',
    )

    print(f'Saved annotation sheet to: {ANNOTATION_SHEET_PATH}')
    print(f'Saved placeholder results to: {RESULTS_PATH}')


if __name__ == '__main__':
    main()

