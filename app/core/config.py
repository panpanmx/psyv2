from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Campus Psy Agent"
    app_env: str = "development"
    log_level: str = "INFO"
    audit_log_path: str = "logs/audit.jsonl"
    database_url: str = "sqlite+aiosqlite:///./campus_psy_agent.db"
    test_database_url: str = "sqlite+aiosqlite:///:memory:"
    knowledge_base_dir: str = "knowledge_base"
    embedding_provider: str = "local"
    rag_top_k: int = 5
    llm_provider: str = "local"
    llm_model: str = "local-rule-model"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_timeout_seconds: int = 30
    llm_signal_extraction_enabled: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
