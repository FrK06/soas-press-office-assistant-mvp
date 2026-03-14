from __future__ import annotations

from uuid import uuid4

from app.config import settings
from app.db import log_enquiry
from app.enquiry.classifier import classify_enquiry
from app.enquiry.verifier import verify_enquiry
from app.llm.grounding import generate_staff_summary
from app.retrieval.expert_ranker import RankerConfig, rank_experts
from app.retrieval.retriever import retrieve_chunks
from app.utils.dates import utcnow
from app.utils.logging import get_logger


logger = get_logger(__name__)


def _build_fallback_staff_summary(
    subject: str,
    body: str,
    topic_labels: list[str],
    experts: list[dict],
) -> str | None:
    if not experts:
        return 'No sufficiently grounded expert recommendations were identified automatically. Manual review is advised.'

    top_names = [expert['name'] for expert in experts[:2]]
    top_name_text = ' and '.join(top_names) if len(top_names) == 2 else top_names[0]

    themes = ', '.join(topic_labels) if topic_labels else 'the enquiry themes'

    strong_reasons = []
    for expert in experts[:3]:
        sections = sorted({chunk['section'] for chunk in expert.get('supporting_chunks', [])})
        if sections:
            strong_reasons.append(f"{expert['name']} ({', '.join(sections)})")

    reasons_text = '; '.join(strong_reasons) if strong_reasons else 'retrieved profile evidence'

    return (
        f'Strongest matches are {top_name_text}, based on grounded profile evidence aligned to {themes}. '
        f'Evidence came from {reasons_text}. '
        'These recommendations should be reviewed by staff before any outreach.'
    )


def process_enquiry(
    sender_name: str,
    sender_email: str,
    outlet_name: str | None,
    subject: str,
    body: str,
    enquiry_id: str | None = None,
    persist_audit: bool = True,
    ranker_config: RankerConfig | None = None,
) -> dict:
    eid = enquiry_id or str(uuid4())
    created_at = utcnow()
    verification = verify_enquiry(sender_email, outlet_name)
    labels = classify_enquiry(subject, body)

    query = f"{subject}\n{body}\nTopics: {', '.join(labels)}"
    chunks = retrieve_chunks(query=query)
    experts = rank_experts(
        chunks,
        top_k=settings.top_k_experts,
        query_text=query,
        topic_labels=labels,
        config=ranker_config,
    )

    if persist_audit:
        log_enquiry(
            enquiry_id=eid,
            sender_name=sender_name,
            sender_email=sender_email,
            outlet_name=outlet_name,
            subject=subject,
            body=body,
            topic_labels=labels,
            verification=verification,
            top_profile_ids=[expert['profile_id'] for expert in experts],
            created_at=created_at.isoformat(),
        )

    summary = _build_fallback_staff_summary(
        subject=subject,
        body=body,
        topic_labels=labels,
        experts=experts,
    )

    if settings.enable_llm_rationales and experts:
        enquiry_text = (
            f'From: {sender_name} <{sender_email}>\n'
            f"Outlet: {outlet_name or 'Unknown'}\n"
            f'Subject: {subject}\n\n{body}'
        )
        try:
            llm_summary = generate_staff_summary(enquiry_text, experts)
        except Exception as exc:
            logger.warning('LLM summary generation failed; falling back to deterministic summary: %s', exc)
        else:
            if llm_summary:
                summary = llm_summary

    return {
        'enquiry_id': eid,
        'created_at': created_at,
        'verification': verification,
        'topic_labels': labels,
        'recommended_experts': experts,
        'requires_staff_approval': True,
        'staff_summary': summary,
    }
