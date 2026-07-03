from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.memory.profile_memory import ProfileMemory


def test_profile_and_report_update_after_chat(tmp_path: Path) -> None:
    app = create_app(
        Settings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'profile.db'}"),
    )
    client = TestClient(app)
    with client:
        client.post(
            "/api/chat/messages",
            json={
                "user_id": "u-profile",
                "conversation_id": "c-profile",
                "message": "最近几周我很低落，睡不好，也不想见同学，但我愿意找朋友聊聊。",
            },
        )
        app.state.services.profile_memory = ProfileMemory()

        profile_response = client.get("/api/profile/u-profile")
        assert profile_response.status_code == 200
        profile = profile_response.json()
        assert "低落" in profile["profile"]["dominant_emotions"]
        assert "朋友支持" in profile["profile"]["protective_factors"]

        timeline_response = client.get("/api/profile/u-profile/timeline")
        assert timeline_response.status_code == 200
        assert timeline_response.json()["risk_timeline"]

        report_response = client.get("/api/report/u-profile/latest")
        assert report_response.status_code == 200
        report = report_response.json()
        assert report["user_id"] == "u-profile"
        assert report["risk_summary"]["depression_risk"] in {"mild", "moderate"}
        assert report["recommended_interventions"]
