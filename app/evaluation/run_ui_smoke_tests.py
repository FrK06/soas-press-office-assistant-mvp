from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib import error, request

DEFAULT_INPUT_PATH = Path('data/evaluation/ui_smoke_test_cases.csv')
DEFAULT_OUTPUT_PATH = Path('data/evaluation/ui_smoke_test_results.csv')
DEFAULT_RAW_OUTPUT_PATH = Path('data/evaluation/ui_smoke_test_results.json')
DEFAULT_BASE_URL = 'http://127.0.0.1:8000'
REQUIRED_COLUMNS = {
    'case_id',
    'category',
    'sender_name',
    'sender_email',
    'outlet_name',
    'subject',
    'body',
    'expected_behavior',
}


@dataclass(frozen=True)
class SmokeCase:
    case_id: str
    category: str
    sender_name: str
    sender_email: str
    outlet_name: str
    subject: str
    body: str
    expected_behavior: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Submit UI smoke-test cases to the local Press Office Assistant API.')
    parser.add_argument('--base-url', default=DEFAULT_BASE_URL)
    parser.add_argument('--input-path', type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument('--output-path', type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument('--raw-output-path', type=Path, default=DEFAULT_RAW_OUTPUT_PATH)
    parser.add_argument('--timeout', type=float, default=30.0)
    parser.add_argument('--case-id', action='append', dest='case_ids', default=[])
    parser.add_argument('--fail-fast', action='store_true')
    return parser.parse_args()


def load_smoke_cases(path: Path, selected_ids: set[str] | None = None) -> list[SmokeCase]:
    if not path.exists():
        raise FileNotFoundError(f'Smoke-test CSV not found: {path}')

    with path.open('r', encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'Missing required smoke-test columns: {sorted(missing)}')

        rows: list[SmokeCase] = []
        for row in reader:
            if not any((value or '').strip() for value in row.values()):
                continue
            case_id = (row['case_id'] or '').strip()
            if selected_ids and case_id not in selected_ids:
                continue
            rows.append(
                SmokeCase(
                    case_id=case_id,
                    category=(row['category'] or '').strip(),
                    sender_name=(row['sender_name'] or '').strip(),
                    sender_email=(row['sender_email'] or '').strip(),
                    outlet_name=(row['outlet_name'] or '').strip(),
                    subject=(row['subject'] or '').strip(),
                    body=(row['body'] or '').strip(),
                    expected_behavior=(row['expected_behavior'] or '').strip(),
                )
            )
    return rows


def build_payload(case: SmokeCase) -> dict[str, Any]:
    return {
        'sender_name': case.sender_name,
        'sender_email': case.sender_email,
        'outlet_name': case.outlet_name,
        'subject': case.subject,
        'body': case.body,
    }


def _response_excerpt(payload: Any) -> str:
    if isinstance(payload, dict):
        for key in ('detail', 'message', 'error'):
            value = payload.get(key)
            if value:
                return str(value)
        return json.dumps(payload, ensure_ascii=False)[:240]
    if payload is None:
        return ''
    return str(payload)[:240]


def summarise_case_result(
    case: SmokeCase,
    status_code: int | None,
    response_payload: Any,
    request_error: str = '',
) -> dict[str, Any]:
    payload = response_payload if isinstance(response_payload, dict) else {}
    verification = payload.get('verification') or {}
    experts = payload.get('recommended_experts') or []
    topic_labels = payload.get('topic_labels') or []
    top_names = [expert.get('name', '') for expert in experts[:3]]
    while len(top_names) < 3:
        top_names.append('')

    return {
        'case_id': case.case_id,
        'category': case.category,
        'sender_email': case.sender_email,
        'outlet_name': case.outlet_name,
        'subject': case.subject,
        'status_code': status_code if status_code is not None else '',
        'request_succeeded': int(bool(status_code and 200 <= status_code < 300 and not request_error)),
        'enquiry_id': payload.get('enquiry_id', ''),
        'recognised_outlet': verification.get('recognised_outlet', ''),
        'manual_review_required': verification.get('manual_review_required', ''),
        'requires_staff_approval': payload.get('requires_staff_approval', ''),
        'recommended_count': len(experts),
        'top_expert_1': top_names[0],
        'top_expert_2': top_names[1],
        'top_expert_3': top_names[2],
        'topic_labels': ' | '.join(topic_labels),
        'expected_behavior': case.expected_behavior,
        'error': request_error or _response_excerpt(response_payload),
    }


def submit_case(case: SmokeCase, base_url: str, timeout: float) -> tuple[int | None, Any, str]:
    url = base_url.rstrip('/') + '/enquiries/process'
    payload = json.dumps(build_payload(case)).encode('utf-8')
    api_request = request.Request(
        url,
        data=payload,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )

    try:
        with request.urlopen(api_request, timeout=timeout) as response:
            body = response.read().decode('utf-8')
            parsed = json.loads(body) if body else {}
            return response.status, parsed, ''
    except error.HTTPError as exc:
        body = exc.read().decode('utf-8', errors='replace')
        try:
            parsed = json.loads(body) if body else {'detail': exc.reason}
        except json.JSONDecodeError:
            parsed = {'detail': body or str(exc.reason)}
        return exc.code, parsed, ''
    except error.URLError as exc:
        return None, None, str(exc.reason)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        raise ValueError('No smoke-test results to write.')
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')


def main() -> None:
    args = parse_args()
    selected_ids = {case_id.strip() for case_id in args.case_ids if case_id.strip()}
    cases = load_smoke_cases(args.input_path, selected_ids or None)
    if not cases:
        raise SystemExit('No smoke-test cases selected.')

    summary_rows: list[dict[str, Any]] = []
    raw_results: list[dict[str, Any]] = []

    for case in cases:
        status_code, response_payload, request_error = submit_case(case, args.base_url, args.timeout)
        summary = summarise_case_result(case, status_code, response_payload, request_error=request_error)
        summary_rows.append(summary)
        raw_results.append(
            {
                'case_id': case.case_id,
                'category': case.category,
                'request_payload': build_payload(case),
                'status_code': status_code,
                'request_error': request_error,
                'response_payload': response_payload,
            }
        )

        if status_code and 200 <= status_code < 300 and not request_error:
            print(f"[{case.case_id}] OK status={status_code} recommended={summary['recommended_count']} top1={summary['top_expert_1']}")
        else:
            print(f"[{case.case_id}] FAILED status={status_code or 'N/A'} error={summary['error']}")
            if args.fail_fast:
                break

    write_csv(args.output_path, summary_rows)
    write_json(
        args.raw_output_path,
        {
            'base_url': args.base_url,
            'input_path': str(args.input_path),
            'output_path': str(args.output_path),
            'raw_output_path': str(args.raw_output_path),
            'results': raw_results,
        },
    )

    success_count = sum(int(row['request_succeeded']) for row in summary_rows)
    print(f'Saved CSV results to: {args.output_path}')
    print(f'Saved raw JSON results to: {args.raw_output_path}')
    print(f'Successful requests: {success_count}/{len(summary_rows)}')


if __name__ == '__main__':
    main()
