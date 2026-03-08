from __future__ import annotations

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.enquiry.approval import record_approval
from app.enquiry.processor import process_enquiry
from app.schemas import ApprovalDecision, MediaEnquiry

app = FastAPI(title="SOAS Press Office Assistant")

templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", response_class=HTMLResponse)
def ui_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/enquiries/process")
def process_media_enquiry(enquiry: MediaEnquiry):
    return process_enquiry(
        sender_name=enquiry.sender_name,
        sender_email=enquiry.sender_email,
        outlet_name=enquiry.outlet_name,
        subject=enquiry.subject,
        body=enquiry.body,
    )


@app.post("/ui/process", response_class=HTMLResponse)
def ui_process(
    request: Request,
    sender_name: str = Form(...),
    sender_email: str = Form(...),
    outlet_name: str = Form(""),
    subject: str = Form(...),
    body: str = Form(...),
):
    result = process_enquiry(
        sender_name=sender_name,
        sender_email=sender_email,
        outlet_name=outlet_name or None,
        subject=subject,
        body=body,
    )
    return templates.TemplateResponse("results.html", {"request": request, "result": result})


@app.post("/enquiries/approval")
def create_approval(decision: ApprovalDecision):
    return record_approval(decision)


@app.post("/ui/approve", response_class=HTMLResponse)
def ui_approve(
    request: Request,
    enquiry_id: str = Form(...),
    decision: str = Form(...),
    reviewer_name: str = Form(...),
    notes: str = Form(""),
):
    payload = ApprovalDecision(
        enquiry_id=enquiry_id,
        decision=decision,
        reviewer_name=reviewer_name,
        notes=notes or None,
    )

    approval = record_approval(
        enquiry_id=payload.enquiry_id,
        decision=payload.decision,
        reviewer_name=payload.reviewer_name,
        notes=payload.notes,
    )

    return templates.TemplateResponse(
        "approval_result.html",
        {"request": request, "approval": approval},
    )