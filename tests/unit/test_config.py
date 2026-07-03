from app.core.config import Settings


def test_settings_exposes_database_urls() -> None:
    settings = Settings(
        database_url="sqlite+aiosqlite:///./dev.db",
        test_database_url="sqlite+aiosqlite:///:memory:",
    )

    assert settings.database_url == "sqlite+aiosqlite:///./dev.db"
    assert settings.test_database_url == "sqlite+aiosqlite:///:memory:"


def test_settings_exposes_rag_configuration() -> None:
    settings = Settings(
        knowledge_base_dir="knowledge_base",
        embedding_provider="local",
        rag_top_k=5,
    )

    assert settings.knowledge_base_dir == "knowledge_base"
    assert settings.embedding_provider == "local"
    assert settings.rag_top_k == 5


def test_settings_exposes_llm_configuration() -> None:
    settings = Settings(
        llm_provider="local",
        llm_model="local-rule-model",
        llm_base_url="https://example.test/v1",
        llm_api_key="test-key",
        llm_timeout_seconds=15,
        llm_signal_extraction_enabled=False,
    )

    assert settings.llm_provider == "local"
    assert settings.llm_model == "local-rule-model"
    assert settings.llm_timeout_seconds == 15
    assert settings.llm_signal_extraction_enabled is False
