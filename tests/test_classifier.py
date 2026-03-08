from app.enquiry.classifier import classify_enquiry


def test_classifier_detects_topics() -> None:
    labels = classify_enquiry('BBC request on migration in the Middle East', 'Looking for an expert on migration and Gaza.')
    assert 'Migration' in labels
    assert 'Middle East' in labels
