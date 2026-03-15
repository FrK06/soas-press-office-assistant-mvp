from app.retrieval.expert_ranker import RankerConfig, rank_experts


def _chunk(**overrides):
    chunk = {
        'chunk_id': 'chunk-1',
        'profile_id': 'expert-a',
        'name': 'Expert A',
        'title': 'Scholar A',
        'department': 'Department A',
        'section': 'research_interests',
        'text': 'Core expertise text.',
        'source_url': 'http://example.com/a',
        'score': 0.7,
        'topics': [],
    }
    chunk.update(overrides)
    return chunk


def test_default_config_matches_explicit_default() -> None:
    chunks = [
        _chunk(
            profile_id='a',
            name='A',
            title='Migration specialist',
            department='Development',
            text='Research on migration and refugee protection with public commentary.',
            score=0.72,
            topics=['Migration'],
        )
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


def test_best_chunk_dominates_many_mediocre_chunks() -> None:
    chunks = [
        _chunk(profile_id='a', name='Expert A', section='biography', score=0.52, text='Broad biography mention.'),
        _chunk(chunk_id='a2', profile_id='a', name='Expert A', section='biography', score=0.52, text='Another broad biography mention.'),
        _chunk(chunk_id='a3', profile_id='a', name='Expert A', section='biography', score=0.51, text='Third broad biography mention.'),
        _chunk(profile_id='b', name='Expert B', section='research_interests', score=0.68, text='Explicit migration governance expertise.'),
    ]

    ranked = rank_experts(
        chunks,
        top_k=2,
        query_text='migration governance',
        query_keyphrases=['migration governance'],
        config=RankerConfig(enable_topic_boosts=False),
    )

    assert ranked[0]['profile_id'] == 'b'


def test_research_interests_match_outranks_publications_only_match() -> None:
    chunks = [
        _chunk(
            profile_id='a',
            name='Expert A',
            section='research_interests',
            text='Migration governance and asylum policy expertise.',
            score=0.64,
        ),
        _chunk(
            profile_id='b',
            name='Expert B',
            section='publications',
            text='Migration governance and asylum policy expertise.',
            score=0.72,
        ),
    ]

    ranked = rank_experts(
        chunks,
        top_k=2,
        query_text='migration governance asylum policy',
        query_keyphrases=['migration governance', 'asylum policy'],
    )

    assert ranked[0]['profile_id'] == 'a'


def test_query_overlap_changes_ordering() -> None:
    chunks = [
        _chunk(
            profile_id='a',
            name='Expert A',
            text='Research on migration governance and asylum systems.',
            score=0.61,
            topics=['Migration'],
        ),
        _chunk(
            profile_id='b',
            name='Expert B',
            text='Strong macroeconomic analysis.',
            score=0.67,
            topics=['Economics'],
        ),
    ]

    no_overlap = rank_experts(
        chunks,
        top_k=2,
        query_text='migration governance',
        query_keyphrases=['migration governance'],
        config=RankerConfig(enable_topic_boosts=False),
    )
    with_overlap = rank_experts(
        chunks,
        top_k=2,
        query_text='migration governance',
        query_keyphrases=['migration governance'],
        config=RankerConfig(enable_topic_boosts=True),
    )

    assert no_overlap[0]['profile_id'] == 'b'
    assert with_overlap[0]['profile_id'] == 'a'


def test_publication_only_evidence_is_penalized() -> None:
    chunks = [
        _chunk(
            profile_id='a',
            name='Expert A',
            section='publications',
            text='List of publications on banking regulation and stability.',
            score=0.78,
        ),
        _chunk(
            profile_id='b',
            name='Expert B',
            section='biography',
            text='Biography describing banking regulation and financial stability work.',
            score=0.84,
        ),
    ]

    ranked = rank_experts(
        chunks,
        top_k=2,
        query_text='banking regulation financial stability',
        query_keyphrases=['banking regulation', 'financial stability'],
        config=RankerConfig(enable_topic_boosts=False),
    )

    assert ranked[0]['profile_id'] == 'b'


def test_media_signal_boost_toggle_changes_ordering() -> None:
    chunks = [
        _chunk(
            profile_id='a',
            name='Expert A',
            text='Frequent media interview and public commentary work on migration governance.',
            score=0.66,
        ),
        _chunk(
            profile_id='b',
            name='Expert B',
            text='Strong legal research record on migration governance.',
            score=0.70,
        ),
    ]

    no_media_boost = rank_experts(
        chunks,
        top_k=2,
        query_text='migration governance',
        query_keyphrases=['migration governance'],
        config=RankerConfig(enable_media_signal_boost=False),
    )
    with_media_boost = rank_experts(
        chunks,
        top_k=2,
        query_text='migration governance',
        query_keyphrases=['migration governance'],
        config=RankerConfig(enable_media_signal_boost=True),
    )

    assert no_media_boost[0]['profile_id'] == 'b'
    assert with_media_boost[0]['profile_id'] == 'a'


def test_diversity_penalty_toggle_changes_ordering() -> None:
    chunks = [
        _chunk(profile_id='a', name='Expert A', score=0.64, text='Political economy expertise one.'),
        _chunk(chunk_id='a2', profile_id='a', name='Expert A', score=0.60, text='Political economy expertise two.'),
        _chunk(chunk_id='a3', profile_id='a', name='Expert A', score=0.58, text='Political economy expertise three.'),
        _chunk(chunk_id='a4', profile_id='a', name='Expert A', score=0.57, text='Political economy expertise four.'),
        _chunk(profile_id='b', name='Expert B', score=0.90, text='Political economy expertise.'),
    ]

    no_penalty = rank_experts(
        chunks,
        top_k=2,
        config=RankerConfig(enable_topic_boosts=False, enable_diversity_penalty=False),
    )
    with_penalty = rank_experts(
        chunks,
        top_k=2,
        config=RankerConfig(enable_topic_boosts=False, enable_diversity_penalty=True),
    )

    assert no_penalty[0]['profile_id'] == 'a'
    assert with_penalty[0]['profile_id'] == 'b'


def test_threshold_config_can_force_abstention() -> None:
    chunks = [
        _chunk(
            profile_id='a',
            name='Expert A',
            text='Economic development expertise.',
            score=0.62,
            topics=['Development'],
        )
    ]

    default_ranked = rank_experts(chunks, top_k=1, config=RankerConfig(enable_topic_boosts=False))
    strict_ranked = rank_experts(
        chunks,
        top_k=1,
        config=RankerConfig(
            enable_topic_boosts=False,
            min_single_chunk_score=0.65,
            min_final_score=0.67,
        ),
    )

    assert len(default_ranked) == 1
    assert strict_ranked == []

def test_strong_exact_phrase_override_allows_valid_research_interest_match_below_single_chunk_threshold() -> None:
    chunks = [
        _chunk(
            profile_id='a',
            name='Expert A',
            section='research_interests',
            text='Development finance and climate finance expertise focused on African economies.',
            score=0.52,
        )
    ]

    ranked = rank_experts(
        chunks,
        top_k=1,
        query_text='development finance climate finance',
        query_keyphrases=['development finance', 'climate finance'],
        config=RankerConfig(min_single_chunk_score=0.55, min_final_score=0.62),
    )

    assert len(ranked) == 1
    assert ranked[0]['profile_id'] == 'a'


def test_low_score_match_without_meaningful_overlap_still_abstains() -> None:
    chunks = [
        _chunk(
            profile_id='a',
            name='Expert A',
            section='research_interests',
            text='Broad governance and institutional analysis.',
            score=0.52,
        )
    ]

    ranked = rank_experts(
        chunks,
        top_k=1,
        query_text='development finance climate finance',
        query_keyphrases=['development finance', 'climate finance'],
        config=RankerConfig(min_single_chunk_score=0.55, min_final_score=0.62),
    )

    assert ranked == []


def test_region_issue_phrases_outperform_generic_region_overlap() -> None:
    chunks = [
        _chunk(
            profile_id='a',
            name='Expert A',
            section='research_interests',
            text='Migration routes and border governance across the Horn of Africa.',
            score=0.50,
        ),
        _chunk(
            profile_id='b',
            name='Expert B',
            section='research_interests',
            text='Africa governance and migration research.',
            score=0.53,
        ),
    ]

    ranked = rank_experts(
        chunks,
        top_k=2,
        query_text='migration routes through the Horn of Africa',
        query_keyphrases=['Horn of Africa', 'migration routes', 'border governance'],
        config=RankerConfig(min_single_chunk_score=0.55, min_final_score=0.62),
    )

    assert ranked[0]['profile_id'] == 'a'
