from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_services
from app.db.repositories.profile_repo import ProfileRepository
from app.db.repositories.risk_repo import RiskRepository
from app.schemas.report import ReportResponse
from app.schemas.risk import RiskResult, RiskSummary, summarize_risk
from app.services import AppServices

router = APIRouter(prefix="/api/report", tags=["report"])


@router.get("/{user_id}/latest", response_model=ReportResponse)
async def latest_report(
    user_id: str,
    services: Annotated[AppServices, Depends(get_services)],
) -> ReportResponse:
    async with services.sessionmaker() as session:
        profile_repo = ProfileRepository(session)
        risk_repo = RiskRepository(session)
        latest = await risk_repo.latest_for_user(user_id)
        if latest is None:
            latest = await profile_repo.get_latest_risk(user_id)
        latest = latest or summarize_risk(RiskResult())
        profile = await profile_repo.get_profile(user_id)
        summary = await profile_repo.get_summary(user_id)
    interventions = _report_interventions(profile, latest)
    return ReportResponse(
        user_id=user_id,
        profile_summary=summary,
        risk_summary=latest,
        evidence_summary=_evidence_summary(profile),
        recommended_interventions=interventions,
        offline_help_recommended=latest.crisis_level in {"s2", "s3", "s4"}
        or latest.depression_risk in {"moderate", "moderately_severe", "severe"},
    )


@router.post("/{user_id}/generate", response_model=ReportResponse)
async def generate_report(
    user_id: str,
    services: Annotated[AppServices, Depends(get_services)],
) -> ReportResponse:
    return await latest_report(user_id, services)


def _evidence_summary(profile: dict[str, list[str]]) -> list[str]:
    evidence: list[str] = []
    for label, key in [
        ("主要情绪", "dominant_emotions"),
        ("压力源", "stressors"),
        ("症状", "symptoms"),
        ("功能受损", "function_impairment"),
        ("保护因素", "protective_factors"),
    ]:
        values = profile.get(key, [])
        if values:
            evidence.append(f"{label}: {'、'.join(values)}")
    return evidence


def _report_interventions(profile: dict[str, list[str]], latest: RiskSummary) -> list[str]:
    actions: list[str] = []
    if latest.anxiety_risk in {"mild", "moderate", "severe"}:
        actions.append("GAD-7 复测与担忧记录")
    if latest.depression_risk in {"mild", "moderate", "moderately_severe", "severe"}:
        actions.append("行为激活与支持系统连接")
    if "失眠" in profile.get("symptoms", []):
        actions.append("睡眠卫生计划")
    if latest.crisis_level in {"s2", "s3", "s4"}:
        actions.append("立即联系可信成年人、学校心理中心或紧急援助")
    return actions or ["持续记录情绪、睡眠和学习状态"]
