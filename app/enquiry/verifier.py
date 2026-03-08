from __future__ import annotations

RECOGNISED_DOMAINS = {
    'bbc.co.uk',
    'theguardian.com',
    'reuters.com',
    'ft.com',
    'channel4.com',
    'itv.com',
    'sky.uk',
}


def verify_enquiry(sender_email: str, outlet_name: str | None = None) -> dict:
    domain = sender_email.split('@')[-1].lower()
    recognised = domain in RECOGNISED_DOMAINS
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
