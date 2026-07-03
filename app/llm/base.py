from typing import Protocol

from pydantic import BaseModel, Field


class LLMUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMResponse(BaseModel):
    content: str
    model: str
    provider: str
    usage: LLMUsage = Field(default_factory=LLMUsage)
    raw: dict[str, object] = Field(default_factory=dict)


class LLMProvider(Protocol):
    async def chat(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        pass

    async def chat_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        pass
