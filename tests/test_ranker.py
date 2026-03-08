from app.retrieval.expert_ranker import rank_experts


def test_ranker_groups_chunks() -> None:
    chunks = [
        {'chunk_id': '1', 'profile_id': 'a', 'name': 'A', 'section': 'bio', 'text': 'x', 'source_url': 'http://x', 'score': 0.8},
        {'chunk_id': '2', 'profile_id': 'a', 'name': 'A', 'section': 'research', 'text': 'y', 'source_url': 'http://x', 'score': 0.7},
        {'chunk_id': '3', 'profile_id': 'b', 'name': 'B', 'section': 'bio', 'text': 'z', 'source_url': 'http://y', 'score': 0.4},
    ]
    ranked = rank_experts(chunks, top_k=2)
    assert ranked[0]['profile_id'] == 'a'
