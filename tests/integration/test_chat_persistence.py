import asyncio
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import Settings
from app.db.models import AuditLog, Message, RiskAssessment, UserProfile
from app.main import create_app


def test_chat_persists_messages_risk_profile_and_crisis_audit(tmp_path: Path) -> None:
    app = create_app(
        Settings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'chat.db'}"),
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/chat/messages",
            json={
                "user_id": "u-crisis",
                "conversation_id": "c-crisis",
                "message": "我不想活了，已经想好了方式，也准备好了工具。",
            },
        )
        assert response.status_code == 200

        async def inspect_db() -> tuple[int, int, int, int]:
            async with app.state.services.sessionmaker() as session:
                messages = (await session.execute(select(Message))).scalars().all()
                risks = (await session.execute(select(RiskAssessment))).scalars().all()
                profiles = (await session.execute(select(UserProfile))).scalars().all()
                audits = (await session.execute(select(AuditLog))).scalars().all()
                return len(messages), len(risks), len(profiles), len(audits)

        message_count, risk_count, profile_count, audit_count = asyncio.run(inspect_db())

    assert message_count == 2
    assert risk_count == 1
    assert profile_count == 1
    assert audit_count >= 2
