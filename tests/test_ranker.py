from app.retrieval.expert_ranker import RankerConfig, rank_experts


def test_ranker_groups_chunks() -> None:
    chunks = [
        {'chunk_id': '1', 'profile_id': 'a', 'name': 'A', 'section': 'bio', 'text': 'x', 'source_url': 'http://x', 'score': 0.8},
        {'chunk_id': '2', 'profile_id': 'a', 'name': 'A', 'section': 'research', 'text': 'y', 'source_url': 'http://x', 'score': 0.7},
        {'chunk_id': '3', 'profile_id': 'b', 'name': 'B', 'section': 'bio', 'text': 'z', 'source_url': 'http://y', 'score': 0.4},
    ]
    ranked = rank_experts(chunks, top_k=2)
    assert ranked[0]['profile_id'] == 'a'


def test_default_config_matches_explicit_default() -> None:
    chunks = [
        {
            'chunk_id': '1',
            'profile_id': 'a',
            'name': 'A',
            'title': 'Migration specialist',
            'department': 'Development',
            'section': 'research',
            'text': 'Research on migration and refugee protection with public commentary.',
            'source_url': 'http://x',
            'score': 0.72,
            'topics': ['Migration'],
        }
    ]

    implicit = rank_experts(chunks, top_k=1, query_text='migration', topic_labels=['Migration'])
    explicit = rank_experts(
        chunks,
        top_k=1,
        query_text='migration',
        topic_labels=['Migration'],
        config=RankerConfig(),
    )

    assert implicit == explicit


def test_topic_boost_toggle_changes_ordering() -> None:
    chunks = [
        {
            'chunk_id': 'a1',
            'profile_id': 'a',
            'name': 'Expert A',
            'title': 'Migration specialist',
            'department': 'Development',
            'section': 'research',
            'text': 'Migration and refugee protection expertise.',
            'source_url': 'http://a',
            'score': 0.64,
            'topics': ['Migration'],
        },
        {
            'chunk_id': 'b1',
            'profile_id': 'b',
            'name': 'Expert B',
            'title': 'Economist',
            'department': 'Economics',
            'section': 'research',
            'text': 'Macroeconomic analysis.',
            'source_url': 'http://b',
            'score': 0.70,
            'topics': ['Economics'],
        },
    ]

    no_topic_boost = rank_experts(
        chunks,
        top_k=2,
        query_text='migration',
        topic_labels=['Migration'],
        config=RankerConfig(enable_topic_boosts=False, enable_media_signal_boost=False, enable_diversity_penalty=False),
    )
    with_topic_boost = rank_experts(
        chunks,
        top_k=2,
        query_text='migration',
        topic_labels=['Migration'],
        config=RankerConfig(enable_topic_boosts=True, enable_media_signal_boost=False, enable_diversity_penalty=False),
    )

    assert no_topic_boost[0]['profile_id'] == 'b'
    assert with_topic_boost[0]['profile_id'] == 'a'


def test_media_signal_boost_toggle_changes_ordering() -> None:
    chunks = [
        {
            'chunk_id': 'a1',
            'profile_id': 'a',
            'name': 'Expert A',
            'title': 'Scholar A',
            'department': 'Media',
            'section': 'engagement',
            'text': 'Frequent media interview and public commentary work.',
            'source_url': 'http://a',
            'score': 0.68,
            'topics': ['Media'],
        },
        {
            'chunk_id': 'b1',
            'profile_id': 'b',
            'name': 'Expert B',
            'title': 'Scholar B',
            'department': 'Law',
            'section': 'research',
            'text': 'Strong legal research record.',
            'source_url': 'http://b',
            'score': 0.70,
            'topics': ['Law'],
        },
    ]

    no_media_boost = rank_experts(
        chunks,
        top_k=2,
        config=RankerConfig(enable_topic_boosts=False, enable_media_signal_boost=False, enable_diversity_penalty=False),
    )
    with_media_boost = rank_experts(
        chunks,
        top_k=2,
        config=RankerConfig(enable_topic_boosts=False, enable_media_signal_boost=True, enable_diversity_penalty=False),
    )

    assert no_media_boost[0]['profile_id'] == 'b'
    assert with_media_boost[0]['profile_id'] == 'a'


def test_diversity_penalty_toggle_changes_ordering() -> None:
    chunks = [
        {
            'chunk_id': 'a1',
            'profile_id': 'a',
            'name': 'Expert A',
            'title': 'Scholar A',
            'department': 'Politics',
            'section': 'research',
            'text': 'Political economy expertise.',
            'source_url': 'http://a',
            'score': 0.23,
            'topics': ['Politics'],
        },
        {
            'chunk_id': 'a2',
            'profile_id': 'a',
            'name': 'Expert A',
            'title': 'Scholar A',
            'department': 'Politics',
            'section': 'research',
            'text': 'Political economy expertise.',
            'source_url': 'http://a',
            'score': 0.23,
            'topics': ['Politics'],
        },
        {
            'chunk_id': 'a3',
            'profile_id': 'a',
            'name': 'Expert A',
            'title': 'Scholar A',
            'department': 'Politics',
            'section': 'research',
            'text': 'Political economy expertise.',
            'source_url': 'http://a',
            'score': 0.22,
            'topics': ['Politics'],
        },
        {
            'chunk_id': 'a4',
            'profile_id': 'a',
            'name': 'Expert A',
            'title': 'Scholar A',
            'department': 'Politics',
            'section': 'research',
            'text': 'Political economy expertise.',
            'source_url': 'http://a',
            'score': 0.22,
            'topics': ['Politics'],
        },
        {
            'chunk_id': 'b1',
            'profile_id': 'b',
            'name': 'Expert B',
            'title': 'Scholar B',
            'department': 'Politics',
            'section': 'research',
            'text': 'Political economy expertise.',
            'source_url': 'http://b',
            'score': 0.86,
            'topics': ['Politics'],
        },
    ]

    no_penalty = rank_experts(
        chunks,
        top_k=2,
        config=RankerConfig(enable_topic_boosts=False, enable_media_signal_boost=False, enable_diversity_penalty=False),
    )
    with_penalty = rank_experts(
        chunks,
        top_k=2,
        config=RankerConfig(enable_topic_boosts=False, enable_media_signal_boost=False, enable_diversity_penalty=True),
    )

    assert no_penalty[0]['profile_id'] == 'a'
    assert with_penalty[0]['profile_id'] == 'b'


def test_threshold_config_can_force_abstention() -> None:
    chunks = [
        {
            'chunk_id': '1',
            'profile_id': 'a',
            'name': 'Expert A',
            'title': 'Scholar A',
            'department': 'Economics',
            'section': 'research',
            'text': 'Economic development expertise.',
            'source_url': 'http://a',
            'score': 0.62,
            'topics': ['Development'],
        }
    ]

    default_ranked = rank_experts(
        chunks,
        top_k=1,
        config=RankerConfig(enable_topic_boosts=False, enable_media_signal_boost=False, enable_diversity_penalty=False),
    )
    strict_ranked = rank_experts(
        chunks,
        top_k=1,
        config=RankerConfig(
            enable_topic_boosts=False,
            enable_media_signal_boost=False,
            enable_diversity_penalty=False,
            min_single_chunk_score=0.65,
            min_final_score=0.67,
        ),
    )

    assert len(default_ranked) == 1
    assert strict_ranked == []
