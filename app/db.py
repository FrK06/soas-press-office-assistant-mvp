from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.config import settings


SCHEMA_SQL = '''
CREATE TABLE IF NOT EXISTS enquiries (
    enquiry_id TEXT PRIMARY KEY,
    sender_name TEXT NOT NULL,
    sender_email TEXT NOT NULL,
    outlet_name TEXT,
    subject TEXT NOT NULL,
    body TEXT NOT NULL,
    topic_labels TEXT NOT NULL,
    verification_json TEXT NOT NULL,
    top_profile_ids TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    enquiry_id TEXT NOT NULL,
    decision TEXT NOT NULL,
    reviewer_name TEXT NOT NULL,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(enquiry_id) REFERENCES enquiries(enquiry_id)
);
'''


def get_connection() -> sqlite3.Connection:
    db_path = Path(settings.sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON')
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


def log_enquiry(
    enquiry_id: str,
    sender_name: str,
    sender_email: str,
    outlet_name: str | None,
    subject: str,
    body: str,
    topic_labels: list[str],
    verification: dict,
    top_profile_ids: list[str],
    created_at: str,
) -> None:
    with get_connection() as conn:
        conn.execute(
            '''
            INSERT OR REPLACE INTO enquiries (
                enquiry_id, sender_name, sender_email, outlet_name, subject, body,
                topic_labels, verification_json, top_profile_ids, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                enquiry_id,
                sender_name,
                sender_email,
                outlet_name,
                subject,
                body,
                json.dumps(topic_labels),
                json.dumps(verification),
                json.dumps(top_profile_ids),
                created_at,
            ),
        )
        conn.commit()


def log_approval(enquiry_id: str, decision: str, reviewer_name: str, notes: str | None, created_at: str) -> None:
    with get_connection() as conn:
        conn.execute(
            '''
            INSERT INTO approvals (enquiry_id, decision, reviewer_name, notes, created_at)
            VALUES (?, ?, ?, ?, ?)
            ''',
            (enquiry_id, decision, reviewer_name, notes, created_at),
        )
        conn.commit()


def get_enquiry(enquiry_id: str) -> dict | None:
    with get_connection() as conn:
        row = conn.execute('SELECT * FROM enquiries WHERE enquiry_id = ?', (enquiry_id,)).fetchone()
        return dict(row) if row else None
