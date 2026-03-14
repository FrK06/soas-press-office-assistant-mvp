import pytest

from app.enquiry.verifier import verify_enquiry


@pytest.mark.parametrize(
    'sender_email',
    [
        'reporter@bbc.co.uk',
        'producer@news.channel4.co.uk',
        'reporter@economist.com',
        'reporter@aljazeera.com',
    ],
)
def test_verify_enquiry_recognises_default_domains(sender_email: str) -> None:
    result = verify_enquiry(sender_email)
    assert result['recognised_outlet'] is True
    assert result['manual_review_required'] is False
    assert result['work_email_domain_match'] is True


def test_verify_enquiry_uses_freelancer_pathway_for_unrecognised_sender() -> None:
    result = verify_enquiry('writer@gmail.com', 'Freelance journalist')
    assert result['recognised_outlet'] is False
    assert result['freelancer_pathway'] is True
    assert result['manual_review_required'] is True


def test_verify_enquiry_marks_personal_email_for_manual_review() -> None:
    result = verify_enquiry('writer@yahoo.com')
    assert result['recognised_outlet'] is False
    assert result['freelancer_pathway'] is False
    assert result['manual_review_required'] is True
