import json

from app.clinical.signal_extractor import SignalExtractor
from app.llm.base import LLMResponse


class LocalProvider:
    provider_name = "local"

    def __init__(self, *, model: str = "local-rule-model") -> None:
        self.model = model
        self.extractor = SignalExtractor()

    async def chat(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        _ = system_prompt
        payload = await self.chat_json(system_prompt=system_prompt, user_prompt=user_prompt)
        return LLMResponse(
            content=json.dumps(payload, ensure_ascii=False),
            model=self.model,
            provider=self.provider_name,
            raw=payload,
        )

    async def chat_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        _ = system_prompt
        signals = self.extractor.extract(user_prompt)
        payload = signals.model_dump()
        payload["provider"] = self.provider_name
        return payload
