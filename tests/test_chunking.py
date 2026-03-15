from app.ingestion.chunking import build_chunks
from app.schemas import ProfileDocument


BASE_PROFILE = {
    'profile_id': 'soas-test-profile',
    'name': 'Test Scholar',
    'title': 'Lecturer',
    'department': 'Department of Development Studies',
    'expertise_topics': ['Migration'],
    'biography': 'Biography text about migration governance and refugee protection.',
    'research_interests': 'Migration governance; refugee protection',
    'languages': ['English'],
    'source_url': 'https://example.com/profile',
    'last_checked': '2026-03-15',
    'content_hash': 'abc123',
}


def test_chunking_filters_low_value_publication_chunks() -> None:
    profile = ProfileDocument.model_validate(
        {
            **BASE_PROFILE,
            'publications': 'https://example.com/paper1 https://example.com/paper2 contact@example.com',
        }
    )

    chunks = build_chunks(profile)

    assert all(chunk.section != 'publications' for chunk in chunks)


def test_chunking_keeps_content_rich_publication_chunks() -> None:
    profile = ProfileDocument.model_validate(
        {
            **BASE_PROFILE,
            'publications': 'Article on migration governance and border regimes in East Africa with detailed analysis of asylum systems and policy change.',
        }
    )

    chunks = build_chunks(profile)

    assert any(chunk.section == 'publications' for chunk in chunks)
