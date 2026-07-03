from app.core.config import Settings
from app.llm.base import LLMProvider
from app.llm.local_provider import LocalProvider
from app.llm.openai_compatible_provider import OpenAICompatibleProvider


def create_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "local" or not settings.llm_api_key:
        return LocalProvider(model=settings.llm_model)
    if provider in {"openai", "qwen", "deepseek"}:
        base_url = settings.llm_base_url or "https://api.openai.com/v1"
        return OpenAICompatibleProvider(
            provider=provider,
            model=settings.llm_model,
            base_url=base_url,
            api_key=settings.llm_api_key,
            timeout_seconds=settings.llm_timeout_seconds,
        )
    return LocalProvider(model=settings.llm_model)
