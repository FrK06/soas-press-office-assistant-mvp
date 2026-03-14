from __future__ import annotations

import json
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_RECOGNISED_OUTLET_DOMAINS = (
    'bbc.co.uk',
    'reuters.com',
    'ft.com',
    'theguardian.com',
    'channel4.co.uk',
    'economist.com',
    'aljazeera.com',
    'itv.com',
    'sky.com',
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    app_name: str = 'SOAS Press Office Assistant'
    app_env: str = 'dev'
    openai_api_key: str | None = None
    openai_base_url: str = 'https://api.openai.com/v1'
    embedding_model: str = 'text-embedding-3-small'
    llm_model: str = 'gpt-4.1-mini'
    chroma_path: str = './chroma_store'
    collection_name: str = 'soas_profiles'
    top_k_chunks: int = 12
    top_k_experts: int = 5
    sqlite_path: str = './press_office.db'
    enable_llm_rationales: bool = False
    max_chunk_chars: int = 800
    chunk_overlap_chars: int = 120
    recognised_outlet_domains: tuple[str, ...] = DEFAULT_RECOGNISED_OUTLET_DOMAINS

    @field_validator('recognised_outlet_domains', mode='before')
    @classmethod
    def parse_recognised_outlet_domains(cls, value: Any) -> tuple[str, ...] | Any:
        if value in (None, ''):
            return DEFAULT_RECOGNISED_OUTLET_DOMAINS

        if isinstance(value, str):
            text = value.strip()
            if not text:
                return DEFAULT_RECOGNISED_OUTLET_DOMAINS

            if text.startswith('['):
                value = json.loads(text)
            else:
                value = [part.strip() for part in text.split(',')]

        if isinstance(value, (list, tuple, set)):
            cleaned = []
            for item in value:
                domain = str(item).strip().lower().lstrip('@')
                if domain and domain not in cleaned:
                    cleaned.append(domain)
            return tuple(cleaned) or DEFAULT_RECOGNISED_OUTLET_DOMAINS

        return value


settings = Settings()
