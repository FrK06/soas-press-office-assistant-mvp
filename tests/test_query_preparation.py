from app.enquiry.query_preparation import prepare_enquiry_query


def test_prepare_enquiry_query_strips_boilerplate_and_generic_tail() -> None:
    prepared = prepare_enquiry_query(
        'Need an expert on UK public law',
        'Looking for academic comment on constitutional litigation. Interested in policy implications, regional context, and current developments.',
    )

    assert prepared.normalized_subject == 'UK public law'
    assert 'Interested in policy implications' not in prepared.normalized_body
    assert prepared.normalized_query == 'UK public law. constitutional litigation'
    assert 'UK public law' in prepared.keyphrases
    assert 'constitutional litigation' in prepared.keyphrases


def test_prepare_enquiry_query_repairs_repeated_conjunctions_and_preserves_phrases() -> None:
    prepared = prepare_enquiry_query(
        'Need an expert on honour crimes and and legal reform',
        'Looking for academic comment on multilingualism, OHADA law, and and education.',
    )

    assert 'and and' not in prepared.normalized_query
    assert 'OHADA law' in prepared.keyphrases
    assert any('honour crimes' in phrase for phrase in prepared.keyphrases)


def test_prepare_enquiry_query_expands_abbreviations_and_preserves_meaningful_legal_phrases() -> None:
    prepared = prepare_enquiry_query(
        'Need an expert on M.E. and IHL',
        'Looking for academic comment on civilian harm and ceasefire diplomacy.',
    )

    assert 'Middle East' in prepared.normalized_query
    assert 'international humanitarian law' in prepared.normalized_query
    assert 'Middle East' in prepared.keyphrases
    assert 'international humanitarian law' in prepared.keyphrases
    assert 'civilian harm' in prepared.keyphrases
    assert 'ceasefire diplomacy' in prepared.keyphrases


def test_prepare_enquiry_query_extracts_finance_and_political_economy_keyphrases() -> None:
    prepared = prepare_enquiry_query(
        'Expert on sovereign debt IMF reform and African development finance',
        'Need comment on debt restructuring, climate finance, and industrial policy in African economies.',
    )

    assert 'sovereign debt' in prepared.keyphrases
    assert 'development finance' in prepared.keyphrases
    assert 'IMF reform' in prepared.keyphrases
    assert 'debt restructuring' in prepared.keyphrases
    assert 'climate finance' in prepared.keyphrases
    assert 'industrial policy' in prepared.keyphrases


def test_prepare_enquiry_query_extracts_region_issue_phrases_for_horn_migration_queries() -> None:
    prepared = prepare_enquiry_query(
        'Expert on migration routes through the Horn of Africa',
        'Need academic comment on migration routes, border governance, and displacement pressures across the Horn of Africa.',
    )

    assert 'Horn of Africa' in prepared.keyphrases
    assert 'migration routes' in prepared.keyphrases
    assert 'border governance' in prepared.keyphrases
