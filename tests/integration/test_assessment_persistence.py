import asyncio
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import Settings
from app.db.models import Assessment, RiskAssessment
from app.main import create_app


def test_phq9_submission_is_persisted_and_item_9_creates_crisis_review_risk(
    tmp_path: Path,
) -> None:
    app = create_app(
        Settings(database_url=f"sqlite+aiosqlite:///{tmp_path / 'assessment.db'}"),
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/assessments/phq9",
            json={
                "user_id": "u-scale",
                "conversation_id": "c-scale",
                "answers": [1, 2, 1, 2, 1, 2, 1, 1, 1],
            },
        )
        assert response.status_code == 200

        async def inspect_db() -> tuple[str, int, str]:
            async with app.state.services.sessionmaker() as session:
                assessment = (await session.execute(select(Assessment))).scalar_one()
                risk = (await session.execute(select(RiskAssessment))).scalar_one()
                return assessment.scale_type, assessment.score or 0, risk.crisis_level

        scale_type, score, crisis_level = asyncio.run(inspect_db())

    assert scale_type == "phq9"
    assert score == 12
    assert crisis_level == "s2"
