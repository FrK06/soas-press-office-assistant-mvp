from fastapi.testclient import TestClient
import sqlite3

from app.config import settings
from app.main import app


def _patch_runtime(monkeypatch, sample_chunks, sample_experts) -> None:
    monkeypatch.setattr(settings, 'enable_llm_rationales', False)
    monkeypatch.setattr('app.enquiry.processor.retrieve_chunks', lambda query: sample_chunks)

    def fake_rank_experts(chunks, top_k=5, query_text='', topic_labels=None, query_keyphrases=None, config=None):
        return sample_experts

    monkeypatch.setattr('app.enquiry.processor.rank_experts', fake_rank_experts)


def test_process_endpoint_initializes_db_and_returns_typed_contract(tmp_path, monkeypatch, enquiry_payload, sample_chunks, sample_experts) -> None:
    db_path = tmp_path / 'press_office.db'
    monkeypatch.setattr(settings, 'sqlite_path', str(db_path))
    _patch_runtime(monkeypatch, sample_chunks, sample_experts)

    with TestClient(app) as client:
        assert db_path.exists()

        response = client.post('/enquiries/process', json=enquiry_payload)
        assert response.status_code == 200

        body = response.json()
        assert body['requires_staff_approval'] is True
        assert body['recommended_experts'][0]['topics'] == ['Migration', 'Middle East']
        assert body['recommended_experts'][0]['confidence'] == 'High'

    with sqlite3.connect(db_path) as conn:
        enquiry_count = conn.execute('SELECT COUNT(*) FROM enquiries').fetchone()[0]

    assert enquiry_count == 1


def test_approval_endpoint_returns_record_and_persists_decision(tmp_path, monkeypatch, enquiry_payload, sample_chunks, sample_experts) -> None:
    db_path = tmp_path / 'press_office.db'
    monkeypatch.setattr(settings, 'sqlite_path', str(db_path))
    _patch_runtime(monkeypatch, sample_chunks, sample_experts)

    with TestClient(app) as client:
        process_response = client.post('/enquiries/process', json=enquiry_payload)
        enquiry_id = process_response.json()['enquiry_id']

        approval_response = client.post(
            '/enquiries/approval',
            json={
                'enquiry_id': enquiry_id,
                'decision': 'approved',
                'reviewer_name': 'Press Officer',
                'notes': 'Proceed with manual outreach.',
            },
        )

        assert approval_response.status_code == 200
        approval = approval_response.json()
        assert approval['enquiry_id'] == enquiry_id
        assert approval['decision'] == 'approved'
        assert approval['reviewer_name'] == 'Press Officer'
        assert approval['notes'] == 'Proceed with manual outreach.'
        assert 'created_at' in approval

    with sqlite3.connect(db_path) as conn:
        approval_count = conn.execute('SELECT COUNT(*) FROM approvals').fetchone()[0]

    assert approval_count == 1
