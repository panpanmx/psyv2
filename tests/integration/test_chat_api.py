from fastapi.testclient import TestClient

from app.core.config import Settings
from app.llm.base import LLMResponse
from app.main import create_app


class FakeChatProvider:
    provider = "fake"

    async def chat(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        assert "校园心理支持助手" in system_prompt
        assert "用户消息：你好" in user_prompt
        return LLMResponse(content="你好，我在。", model="fake", provider="fake")

    async def chat_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        return {
            "emotions": [],
            "symptoms": [],
            "duration": None,
            "frequency": None,
            "stressors": [],
            "function_impairment": [],
            "risk_markers": [],
            "protective_factors": [],
        }


def test_chat_api_returns_risk_actions_and_follow_up() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/chat/messages",
        json={
            "user_id": "u-001",
            "conversation_id": "c-001",
            "message": "我最近两周考试压力很大，晚上总是睡不着，白天注意力下降。",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["assistant_message"]
    assert body["risk_summary"]["anxiety_risk"] == "moderate"
    assert body["risk_summary"]["crisis_level"] == "s0"
    assert "完成一次 GAD-7 筛查" in body["suggested_actions"]
    assert body["follow_up_questions"]
    assert response.headers["x-request-id"]


def test_chat_api_uses_crisis_response_for_high_risk_message() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/chat/messages",
        json={
            "user_id": "u-crisis",
            "conversation_id": "c-crisis",
            "message": "我不想活了，已经想好了方式，也准备好了工具。",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["risk_summary"]["crisis_level"] in {"s3", "s4"}
    assert "请立刻联系" in body["assistant_message"]
    assert "联系可信成年人或学校心理中心" in body["suggested_actions"]


def test_chat_api_uses_llm_provider_for_normal_response(monkeypatch, tmp_path) -> None:
    monkeypatch.setattr("app.services.create_llm_provider", lambda settings: FakeChatProvider())
    app = create_app(Settings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'chat.db'}"))

    with TestClient(app) as client:
        response = client.post(
            "/api/chat/messages",
            json={
                "user_id": "u-llm-response",
                "conversation_id": "c-llm-response",
                "message": "你好",
            },
        )

    assert response.status_code == 200
    assert response.json()["assistant_message"] == "你好，我在。"
