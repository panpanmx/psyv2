from typing import cast
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RiskAssessment
from app.schemas.risk import (
    AnxietyRisk,
    CrisisLevel,
    DepressionRisk,
    GenericRisk,
    RiskResult,
    RiskSummary,
)


class RiskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_risk(
        self,
        *,
        user_id: str,
        conversation_id: str | None,
        message_id: str | None,
        risk: RiskResult,
    ) -> RiskAssessment:
        row = RiskAssessment(
            id=f"risk_{uuid4().hex}",
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            depression_risk=risk.depression_risk,
            anxiety_risk=risk.anxiety_risk,
            sleep_risk=risk.sleep_risk,
            crisis_level=risk.crisis_level,
            function_impairment_level=risk.function_impairment_level,
            evidence=risk.evidence,
            recommended_next_step=risk.recommended_next_step,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def latest_for_user(self, user_id: str) -> RiskSummary | None:
        result = await self.session.execute(
            select(RiskAssessment)
            .where(RiskAssessment.user_id == user_id)
            .order_by(RiskAssessment.created_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return to_summary(row)

    async def timeline_for_user(self, user_id: str) -> list[dict[str, str]]:
        result = await self.session.execute(
            select(RiskAssessment)
            .where(RiskAssessment.user_id == user_id)
            .order_by(RiskAssessment.created_at)
        )
        return [to_summary(row).model_dump() for row in result.scalars()]


def to_summary(row: RiskAssessment) -> RiskSummary:
    return RiskSummary(
        depression_risk=cast(DepressionRisk, row.depression_risk),
        anxiety_risk=cast(AnxietyRisk, row.anxiety_risk),
        sleep_risk=cast(GenericRisk, row.sleep_risk),
        crisis_level=cast(CrisisLevel, row.crisis_level),
        function_impairment_level=cast(GenericRisk, row.function_impairment_level),
    )
