import json

import httpx

from app.llm.base import LLMResponse, LLMUsage


class OpenAICompatibleProvider:
    def __init__(
        self,
        *,
        provider: str,
        model: str,
        base_url: str,
        api_key: str,
        timeout_seconds: int = 30,
    ) -> None:
        self.provider = provider
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    async def chat(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
            )
            response.raise_for_status()
        raw = response.json()
        content = _content_from_response(raw)
        usage = raw.get("usage", {})
        return LLMResponse(
            content=content,
            model=self.model,
            provider=self.provider,
            usage=LLMUsage(
                prompt_tokens=int(usage.get("prompt_tokens", 0)),
                completion_tokens=int(usage.get("completion_tokens", 0)),
                total_tokens=int(usage.get("total_tokens", 0)),
            ),
            raw=raw,
        )

    async def chat_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        result = await self.chat(system_prompt=system_prompt, user_prompt=user_prompt)
        parsed = json.loads(result.content)
        if not isinstance(parsed, dict):
            raise ValueError("LLM JSON response must be an object")
        return parsed


def _content_from_response(raw: dict[str, object]) -> str:
    choices = raw.get("choices", [])
    if not isinstance(choices, list) or not choices:
        return ""
    first = choices[0]
    if not isinstance(first, dict):
        return ""
    message = first.get("message", {})
    if not isinstance(message, dict):
        return ""
    content = message.get("content", "")
    return content if isinstance(content, str) else ""
