from __future__ import annotations

from pathlib import Path

from app.evaluation.run_ui_smoke_tests import SmokeCase, build_payload, load_smoke_cases, summarise_case_result


SAMPLE_CASE = SmokeCase(
    case_id='UI001',
    category='strong_match',
    sender_name='Jane Reporter',
    sender_email='jane@bbc.co.uk',
    outlet_name='BBC News',
    subject='Expert on Gaza ceasefire and humanitarian law',
    body='Looking for academic comment on civilian protection and humanitarian access.',
    expected_behavior='Should return a strong shortlist.',
)


def test_build_payload_matches_api_shape() -> None:
    payload = build_payload(SAMPLE_CASE)
    assert payload == {
        'sender_name': 'Jane Reporter',
        'sender_email': 'jane@bbc.co.uk',
        'outlet_name': 'BBC News',
        'subject': 'Expert on Gaza ceasefire and humanitarian law',
        'body': 'Looking for academic comment on civilian protection and humanitarian access.',
    }


def test_summarise_case_result_extracts_core_fields() -> None:
    summary = summarise_case_result(
        SAMPLE_CASE,
        200,
        {
            'enquiry_id': 'abc123',
            'verification': {
                'recognised_outlet': True,
                'manual_review_required': False,
            },
            'requires_staff_approval': True,
            'topic_labels': ['Middle East', 'Politics'],
            'recommended_experts': [
                {'name': 'Professor Example'},
                {'name': 'Dr Example Two'},
            ],
        },
    )
    assert summary['request_succeeded'] == 1
    assert summary['recommended_count'] == 2
    assert summary['top_expert_1'] == 'Professor Example'
    assert summary['top_expert_2'] == 'Dr Example Two'
    assert summary['top_expert_3'] == ''
    assert summary['topic_labels'] == 'Middle East | Politics'
    assert summary['recognised_outlet'] is True
    assert summary['manual_review_required'] is False


def test_load_smoke_cases_filters_by_case_id(tmp_path: Path) -> None:
    csv_path = tmp_path / 'smoke.csv'
    csv_path.write_text(
        'case_id,category,sender_name,sender_email,outlet_name,subject,body,expected_behavior\n'
        'UI001,strong,Jane,jane@bbc.co.uk,BBC,Subject one,Body one,Expectation one\n'
        'UI002,strong,Tom,tom@reuters.com,Reuters,Subject two,Body two,Expectation two\n',
        encoding='utf-8',
    )

    rows = load_smoke_cases(csv_path, {'UI002'})
    assert [row.case_id for row in rows] == ['UI002']
    assert rows[0].subject == 'Subject two'
