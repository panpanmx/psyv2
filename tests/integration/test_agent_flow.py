from fastapi.testclient import TestClient

from app.main import create_app


def test_agent_flow_handles_support_and_assessment_suggestions() -> None:
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/chat/messages",
            json={
                "user_id": "flow-u-1",
                "conversation_id": "flow-c-1",
                "message": "我最近两周考试压力很大，晚上睡不着，白天注意力下降。",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["risk_summary"]["anxiety_risk"] == "moderate"
    assert "GAD-7" in payload["suggested_actions"]


def test_agent_flow_routes_depression_and_crisis() -> None:
    with TestClient(create_app()) as client:
        depression = client.post(
            "/api/chat/messages",
            json={
                "user_id": "flow-u-2",
                "conversation_id": "flow-c-2",
                "message": "我最近两周很低落，没兴趣，也很疲惫。",
            },
        )
        crisis = client.post(
            "/api/chat/messages",
            json={
                "user_id": "flow-u-3",
                "conversation_id": "flow-c-3",
                "message": "我不想活了，已经想好了方式。",
            },
        )

    assert depression.status_code == 200
    assert "PHQ-9" in depression.json()["suggested_actions"]
    assert crisis.status_code == 200
    assert crisis.json()["risk_summary"]["crisis_level"] in {"s3", "s4"}
