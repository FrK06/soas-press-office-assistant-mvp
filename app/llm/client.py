from __future__ import annotations

from openai import OpenAI

from app.config import settings


def get_openai_client() -> OpenAI:
    kwargs = {}
    if settings.openai_api_key:
        kwargs['api_key'] = settings.openai_api_key
    if settings.openai_base_url:
        kwargs['base_url'] = settings.openai_base_url
    return OpenAI(**kwargs)
