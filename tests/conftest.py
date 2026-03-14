from __future__ import annotations

import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture
def enquiry_payload() -> dict[str, str]:
    return {
        'sender_name': 'Jane Reporter',
        'sender_email': 'jane@bbc.co.uk',
        'outlet_name': 'BBC News',
        'subject': 'Need an expert on migration and Gaza',
        'body': 'Looking for an academic comment on displacement, migration governance, and regional political implications.',
    }


@pytest.fixture
def sample_chunks() -> list[dict]:
    return [
        {
            'chunk_id': 'soas-dr-anna-lindley-chunk-1',
            'profile_id': 'soas-dr-anna-lindley',
            'name': 'Dr Anna Lindley',
            'title': 'Reader in Migration, Mobility and Development',
            'department': 'Department of Development Studies',
            'section': 'biography',
            'text': 'Anna Lindley researches migration, refugee protection, displacement, and the politics of border regimes.',
            'source_url': 'https://example.com/anna-lindley',
            'score': 0.91,
            'topics': ['Migration', 'Middle East'],
        }
    ]


@pytest.fixture
def sample_experts(sample_chunks: list[dict]) -> list[dict]:
    return [
        {
            'profile_id': 'soas-dr-anna-lindley',
            'name': 'Dr Anna Lindley',
            'title': 'Reader in Migration, Mobility and Development',
            'department': 'Department of Development Studies',
            'source_url': 'https://example.com/anna-lindley',
            'rationale': 'Matched on retrieved evidence from biography. Recommendation is grounded in profile content and should be reviewed by staff before outreach.',
            'supporting_chunks': sample_chunks,
            'final_score': 1.24,
            'topics': ['Migration', 'Middle East'],
            'confidence': 'High',
            'diversity_note': None,
        }
    ]
