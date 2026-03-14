from app.enquiry.classifier import classify_enquiry


def test_classifier_detects_topics() -> None:
    labels = classify_enquiry(
        'BBC request on migration in the Middle East',
        'Looking for an expert on migration, Gaza, and asylum governance.',
    )
    assert 'Migration' in labels
    assert 'Middle East' in labels


def test_classifier_ignores_generic_policy_boilerplate() -> None:
    labels = classify_enquiry(
        'General request',
        'Interested in policy implications, regional context, and current developments.',
    )
    assert labels == ['General']
