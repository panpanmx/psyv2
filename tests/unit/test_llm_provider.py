from app.core.config import Settings
from app.db.session import create_sessionmaker
from app.llm.local_provider import LocalProvider
from app.llm.provider_factory import create_llm_provider
from app.services import AppServices


async def test_local_provider_returns_deterministic_structured_response() -> None:
    provider = LocalProvider(model="local-rule-model")

    result = await provider.chat_json(
        system_prompt="extract",
        user_prompt="我最近两周很低落，睡不着。",
    )

    assert result["provider"] == "local"
    assert "低落" in result["emotions"]


def test_provider_factory_defaults_to_local_without_key() -> None:
    provider = create_llm_provider(Settings(llm_provider="openai", llm_api_key=""))

    assert isinstance(provider, LocalProvider)


def test_app_services_can_disable_llm_signal_extraction(tmp_path) -> None:
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'services.db'}",
        llm_provider="openai",
        llm_api_key="test-key",
        llm_signal_extraction_enabled=False,
    )

    services = AppServices(settings, create_sessionmaker(settings))

    assert services.llm_signal_extractor is None
    assert services.llm_provider is not None
