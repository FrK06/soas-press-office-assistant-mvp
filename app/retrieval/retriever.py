from __future__ import annotations

from app.config import settings
from app.retrieval.embedder import Embedder
from app.retrieval.store import get_collection


def retrieve_chunks(query: str, top_k: int | None = None) -> list[dict]:
    top_k = top_k or settings.top_k_chunks
    embedder = Embedder()
    collection = get_collection()
    query_embedding = embedder.embed_text(query)

    results = collection.query(query_embeddings=[query_embedding], n_results=top_k)
    ids = results['ids'][0]
    docs = results['documents'][0]
    metas = results['metadatas'][0]
    distances = results.get('distances', [[0.0] * len(ids)])[0]

    output: list[dict] = []
    for chunk_id, doc, meta, distance in zip(ids, docs, metas, distances):
        topics = [topic.strip() for topic in (meta.get('topics') or '').split(',') if topic.strip()]
        score = max(0.0, 1 / (1 + distance))

        output.append(
            {
                'chunk_id': chunk_id,
                'profile_id': meta['profile_id'],
                'name': meta['name'],
                'title': meta.get('title') or None,
                'department': meta.get('department') or None,
                'section': meta.get('section') or 'unknown',
                'source_url': meta['source_url'],
                'text': doc,
                'score': score,
                'topics': topics,
            }
        )

    return output
