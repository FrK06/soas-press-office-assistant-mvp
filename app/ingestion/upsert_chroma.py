from __future__ import annotations

from app.ingestion.chunking import build_chunks
from app.ingestion.parse_profiles import load_processed_profiles
from app.retrieval.embedder import Embedder
from app.retrieval.store import get_collection


def upsert_profiles() -> int:
    profiles = load_processed_profiles()
    embedder = Embedder()
    collection = get_collection()

    total = 0
    for profile in profiles:
        chunks = build_chunks(profile)
        if not chunks:
            continue

        ids = [chunk.chunk_id for chunk in chunks]
        documents = [chunk.text for chunk in chunks]
        metadatas = [
            {
                'profile_id': chunk.profile_id,
                'name': chunk.name,
                'department': chunk.department or '',
                'title': chunk.title or '',
                'section': chunk.section,
                'source_url': str(chunk.source_url),
                'topics': ', '.join(chunk.topics),
                'last_checked': chunk.last_checked,
                'content_hash': chunk.content_hash,
            }
            for chunk in chunks
        ]
        embeddings = [embedder.embed_text(text) for text in documents]
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
        total += len(chunks)
    return total


if __name__ == '__main__':
    inserted = upsert_profiles()
    print(f'Upserted {inserted} chunks')
