from __future__ import annotations

from app.config import settings
from app.llm.client import get_openai_client


class Embedder:
    def __init__(self) -> None:
        self.client = get_openai_client()

    def embed_text(self, text: str) -> list[float]:
        response = self.client.embeddings.create(model=settings.embedding_model, input=text)
        return response.data[0].embedding
