from __future__ import annotations

from app.config import settings


def _normalize_domain(value: str) -> str:
    return value.strip().lower().lstrip('@')


def _domain_in_allowlist(domain: str, allowlist: tuple[str, ...]) -> bool:
    return any(domain == allowed or domain.endswith(f'.{allowed}') for allowed in allowlist)


def verify_enquiry(sender_email: str, outlet_name: str | None = None) -> dict:
    domain = _normalize_domain(sender_email.split('@')[-1])
    recognised = _domain_in_allowlist(domain, settings.recognised_outlet_domains)
    freelancer_pathway = not recognised and bool(outlet_name)
    manual_review_required = not recognised
    notes = (
        'Recognised outlet work email detected.'
        if recognised
        else 'Use freelancer pathway or route to manual handling for verification.'
    )
    return {
        'recognised_outlet': recognised,
        'work_email_domain_match': recognised,
        'freelancer_pathway': freelancer_pathway,
        'manual_review_required': manual_review_required,
        'notes': notes,
    }
