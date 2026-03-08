from __future__ import annotations

from fastapi import FastAPI, HTTPException

from app.db import get_enquiry, init_db
from app.enquiry.approval import record_approval
from app.enquiry.processor import process_enquiry
from app.schemas import ApprovalDecision, MediaEnquiry

app = FastAPI(title='SOAS Press Office Assistant')


@app.on_event('startup')
def startup() -> None:
    init_db()


@app.get('/health')
def health() -> dict:
    return {'status': 'ok'}


@app.post('/enquiries/process')
def process_media_enquiry(enquiry: MediaEnquiry) -> dict:
    return process_enquiry(
        sender_name=enquiry.sender_name,
        sender_email=str(enquiry.sender_email),
        outlet_name=enquiry.outlet_name,
        subject=enquiry.subject,
        body=enquiry.body,
        enquiry_id=enquiry.enquiry_id,
    )


@app.post('/enquiries/approval')
def submit_approval(decision: ApprovalDecision) -> dict:
    existing = get_enquiry(decision.enquiry_id)
    if not existing:
        raise HTTPException(status_code=404, detail='Enquiry not found')
    return record_approval(
        enquiry_id=decision.enquiry_id,
        decision=decision.decision,
        reviewer_name=decision.reviewer_name,
        notes=decision.notes,
    )


@app.get('/enquiries/{enquiry_id}')
def fetch_enquiry(enquiry_id: str) -> dict:
    item = get_enquiry(enquiry_id)
    if not item:
        raise HTTPException(status_code=404, detail='Enquiry not found')
    return item
