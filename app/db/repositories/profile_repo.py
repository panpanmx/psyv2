from typing import cast
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserProfile
from app.schemas.risk import (
    AnxietyRisk,
    CrisisLevel,
    DepressionRisk,
    ExtractedSignals,
    GenericRisk,
    RiskResult,
    RiskSummary,
    summarize_risk,
)

DEFAULT_PROFILE: dict[str, list[str]] = {
    "dominant_emotions": [],
    "stressors": [],
    "symptoms": [],
    "function_impairment": [],
    "protective_factors": [],
    "risk_factors": [],
}


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def update_profile(
        self,
        *,
        user_id: str,
        signals: ExtractedSignals,
        risk: RiskResult,
        message_id: str | None,
    ) -> UserProfile:
        profile = await self._get_or_create(user_id)
        profile_data = normalize_profile(profile.profile_json)
        merge_unique(profile_data["dominant_emotions"], signals.emotions)
        merge_unique(profile_data["stressors"], signals.stressors)
        merge_unique(profile_data["symptoms"], signals.symptoms)
        merge_unique(profile_data["function_impairment"], signals.function_impairment)
        merge_unique(profile_data["protective_factors"], signals.protective_factors)
        merge_unique(profile_data["risk_factors"], signals.risk_markers)
        profile.profile_json = profile_data
        profile.latest_summary = summarize_profile(profile_data)
        timeline = list(profile.risk_trend_json or [])
        timeline.append(summarize_risk(risk).model_dump())
        profile.risk_trend_json = timeline
        profile.updated_by_message_id = message_id
        await self.session.flush()
        return profile

    async def get_profile(self, user_id: str) -> dict[str, list[str]]:
        profile = await self._get_or_create(user_id)
        return normalize_profile(profile.profile_json)

    async def get_summary(self, user_id: str) -> str:
        profile = await self._get_or_create(user_id)
        return profile.latest_summary or "尚未形成足够画像。"

    async def get_latest_risk(self, user_id: str) -> RiskSummary | None:
        profile = await self._get_or_create(user_id)
        timeline = list(profile.risk_trend_json or [])
        if not timeline:
            return None
        latest = timeline[-1]
        return RiskSummary(
            depression_risk=cast(DepressionRisk, latest["depression_risk"]),
            anxiety_risk=cast(AnxietyRisk, latest["anxiety_risk"]),
            sleep_risk=cast(GenericRisk, latest["sleep_risk"]),
            crisis_level=cast(CrisisLevel, latest["crisis_level"]),
            function_impairment_level=cast(GenericRisk, latest["function_impairment_level"]),
        )

    async def get_timeline(self, user_id: str) -> list[dict[str, str]]:
        profile = await self._get_or_create(user_id)
        return list(profile.risk_trend_json or [])

    async def _get_or_create(self, user_id: str) -> UserProfile:
        result = await self.session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            return existing
        profile = UserProfile(
            id=f"profile_{uuid4().hex}",
            user_id=user_id,
            profile_json=normalize_profile({}),
            latest_summary="尚未形成足够画像。",
            risk_trend_json=[],
        )
        self.session.add(profile)
        await self.session.flush()
        return profile


def normalize_profile(raw: object) -> dict[str, list[str]]:
    if not isinstance(raw, dict):
        raw = {}
    return {key: list(raw.get(key, [])) for key in DEFAULT_PROFILE}


def merge_unique(target: list[str], values: list[str]) -> None:
    for value in values:
        if value not in target:
            target.append(value)


def summarize_profile(profile: dict[str, list[str]]) -> str:
    emotions = "、".join(profile["dominant_emotions"]) or "暂无明显情绪主题"
    stressors = "、".join(profile["stressors"]) or "暂无明确压力源"
    return f"近期主要情绪：{emotions}；主要压力源：{stressors}。"
