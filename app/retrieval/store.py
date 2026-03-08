from __future__ import annotations

import chromadb

from app.config import settings


def get_collection():
    client = chromadb.PersistentClient(path=settings.chroma_path)
    return client.get_or_create_collection(settings.collection_name)
