from __future__ import annotations

from app.db import log_approval
from app.utils.dates import utcnow


def record_approval(enquiry_id: str, decision: str, reviewer_name: str, notes: str | None = None) -> dict:
    created_at = utcnow()
    log_approval(
        enquiry_id=enquiry_id,
        decision=decision,
        reviewer_name=reviewer_name,
        notes=notes,
        created_at=created_at.isoformat(),
    )
    return {
        'enquiry_id': enquiry_id,
        'decision': decision,
        'reviewer_name': reviewer_name,
        'notes': notes,
        'created_at': created_at,
    }
