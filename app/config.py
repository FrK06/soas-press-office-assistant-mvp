from pydantic_settings import BaseSettings, SettingsConfigDict


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


settings = Settings()
