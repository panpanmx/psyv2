from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Assessment


class AssessmentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_assessment(
        self,
        *,
        user_id: str,
        conversation_id: str | None,
        scale_type: str,
        answers: list[int] | dict[str, Any],
        score: int | None,
        severity: str,
        interpretation: str,
    ) -> Assessment:
        row = Assessment(
            id=f"assessment_{uuid4().hex}",
            user_id=user_id,
            conversation_id=conversation_id,
            scale_type=scale_type,
            answers=answers,
            score=score,
            severity=severity,
            interpretation=interpretation,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def list_for_user(self, user_id: str, *, limit: int = 20) -> list[Assessment]:
        result = await self.session.execute(
            select(Assessment)
            .where(Assessment.user_id == user_id)
            .order_by(Assessment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars())

    async def latest_for_user(self, user_id: str, scale_type: str) -> Assessment | None:
        result = await self.session.execute(
            select(Assessment)
            .where(Assessment.user_id == user_id, Assessment.scale_type == scale_type)
            .order_by(Assessment.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
