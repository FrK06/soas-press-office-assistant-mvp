import sqlite3

from app.config import settings
from app.db import init_db
from app.enquiry.processor import process_enquiry
from app.evaluation.common import EvalCase, evaluate_case


def _patch_retrieval(monkeypatch, sample_chunks, sample_experts) -> None:
    monkeypatch.setattr('app.enquiry.processor.retrieve_chunks', lambda query: sample_chunks)

    def fake_rank_experts(chunks, top_k=5, query_text='', topic_labels=None, query_keyphrases=None, config=None):
        return sample_experts

    monkeypatch.setattr('app.enquiry.processor.rank_experts', fake_rank_experts)


def test_process_enquiry_skips_audit_logging_when_disabled(tmp_path, monkeypatch, sample_chunks, sample_experts) -> None:
    db_path = tmp_path / 'press_office.db'
    monkeypatch.setattr(settings, 'sqlite_path', str(db_path))
    monkeypatch.setattr(settings, 'enable_llm_rationales', False)
    _patch_retrieval(monkeypatch, sample_chunks, sample_experts)
    init_db()

    process_enquiry(
        sender_name='Jane Reporter',
        sender_email='jane@bbc.co.uk',
        outlet_name='BBC News',
        subject='Need an expert on migration and Gaza',
        body='Looking for comment on displacement and refugee protection.',
        persist_audit=False,
    )

    with sqlite3.connect(db_path) as conn:
        first_count = conn.execute('SELECT COUNT(*) FROM enquiries').fetchone()[0]

    process_enquiry(
        sender_name='Jane Reporter',
        sender_email='jane@bbc.co.uk',
        outlet_name='BBC News',
        subject='Need an expert on migration and Gaza',
        body='Looking for comment on displacement and refugee protection.',
        persist_audit=True,
    )

    with sqlite3.connect(db_path) as conn:
        second_count = conn.execute('SELECT COUNT(*) FROM enquiries').fetchone()[0]

    assert first_count == 0
    assert second_count == 1


def test_evaluate_case_disables_audit_logging(monkeypatch, sample_experts) -> None:
    captured = {}

    def fake_process_enquiry(**kwargs):
        captured.update(kwargs)
        return {
            'enquiry_id': kwargs['enquiry_id'],
            'created_at': '2026-03-14T12:00:00+00:00',
            'verification': {
                'recognised_outlet': True,
                'work_email_domain_match': True,
                'freelancer_pathway': False,
                'manual_review_required': False,
                'notes': 'Recognised outlet work email detected.',
            },
            'topic_labels': ['Migration'],
            'recommended_experts': sample_experts,
            'requires_staff_approval': True,
            'staff_summary': 'Fallback summary',
        }

    monkeypatch.setattr('app.evaluation.common.process_enquiry', fake_process_enquiry)

    case = EvalCase(
        test_id='T001',
        sender_name='Jane Reporter',
        sender_email='jane@bbc.co.uk',
        outlet_name='BBC News',
        subject='Need an expert on migration and Gaza',
        body='Looking for comment on displacement and refugee protection.',
        expected_experts=['dr anna lindley'],
    )

    result = evaluate_case(case)

    assert captured['persist_audit'] is False
    assert result['top1_hit'] == 1


def test_process_enquiry_falls_back_when_llm_summary_fails(tmp_path, monkeypatch, sample_chunks, sample_experts) -> None:
    db_path = tmp_path / 'press_office.db'
    monkeypatch.setattr(settings, 'sqlite_path', str(db_path))
    monkeypatch.setattr(settings, 'enable_llm_rationales', True)
    _patch_retrieval(monkeypatch, sample_chunks, sample_experts)
    init_db()

    def raise_llm_error(enquiry_text, experts):
        raise RuntimeError('provider unavailable')

    monkeypatch.setattr('app.enquiry.processor.generate_staff_summary', raise_llm_error)

    result = process_enquiry(
        sender_name='Jane Reporter',
        sender_email='jane@bbc.co.uk',
        outlet_name='BBC News',
        subject='Need an expert on migration and Gaza',
        body='Looking for comment on displacement and refugee protection.',
        persist_audit=False,
    )

    assert result['staff_summary'].startswith('Strongest matches are Dr Anna Lindley')

