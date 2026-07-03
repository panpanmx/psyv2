from typing import Annotated, Any, cast

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_request_id, get_services
from app.clinical.scales.cssrs_like import score_crisis_screen
from app.clinical.scales.gad7 import score_gad7
from app.clinical.scales.phq9 import score_phq9
from app.db.repositories.assessment_repo import AssessmentRepository
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.conversation_repo import ConversationRepository
from app.db.repositories.risk_repo import RiskRepository
from app.observability.events import SAFETY_ESCALATION_TRIGGERED
from app.schemas.assessment import CrisisScreenRequest, ScaleAnswersRequest, ScaleScoreResponse
from app.schemas.risk import AnxietyRisk, DepressionRisk, RiskResult
from app.services import AppServices

router = APIRouter(prefix="/api/assessments", tags=["assessments"])


@router.post("/phq9", response_model=ScaleScoreResponse)
async def submit_phq9(
    payload: ScaleAnswersRequest,
    services: Annotated[AppServices, Depends(get_services)],
) -> ScaleScoreResponse:
    try:
        result = score_phq9(payload.answers)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    async with services.sessionmaker() as session:
        await _ensure_scope(session, payload.user_id, payload.conversation_id)
        assessment_repo = AssessmentRepository(session)
        risk_repo = RiskRepository(session)
        await assessment_repo.save_assessment(
            user_id=payload.user_id,
            conversation_id=payload.conversation_id,
            scale_type="phq9",
            answers=payload.answers,
            score=result.score,
            severity=result.severity,
            interpretation=result.interpretation,
        )
        if result.item_9_positive:
            await risk_repo.save_risk(
                user_id=payload.user_id,
                conversation_id=payload.conversation_id,
                message_id=None,
                risk=RiskResult(
                    depression_risk=cast_depression_risk(result.severity),
                    crisis_level="s2",
                    evidence=[{"source": "phq9", "detail": "PHQ-9 第 9 题阳性"}],
                    recommended_next_step={
                        "route": "crisis_review",
                        "summary": "PHQ-9 第 9 题阳性，建议危机复核",
                    },
                ),
            )
        await session.commit()
    return ScaleScoreResponse(
        scale_type="phq9",
        score=result.score,
        severity=result.severity,
        interpretation=result.interpretation,
        recommended_next_step=result.recommended_next_step,
    )


@router.post("/gad7", response_model=ScaleScoreResponse)
async def submit_gad7(
    payload: ScaleAnswersRequest,
    services: Annotated[AppServices, Depends(get_services)],
) -> ScaleScoreResponse:
    try:
        result = score_gad7(payload.answers)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    async with services.sessionmaker() as session:
        await _ensure_scope(session, payload.user_id, payload.conversation_id)
        assessment_repo = AssessmentRepository(session)
        risk_repo = RiskRepository(session)
        await assessment_repo.save_assessment(
            user_id=payload.user_id,
            conversation_id=payload.conversation_id,
            scale_type="gad7",
            answers=payload.answers,
            score=result.score,
            severity=result.severity,
            interpretation=result.interpretation,
        )
        if result.severity in {"moderate", "severe"}:
            await risk_repo.save_risk(
                user_id=payload.user_id,
                conversation_id=payload.conversation_id,
                message_id=None,
                risk=RiskResult(
                    anxiety_risk=cast_anxiety_risk(result.severity),
                    evidence=[{"source": "gad7", "detail": f"GAD-7 分数 {result.score}"}],
                    recommended_next_step={
                        "route": "assessment",
                        "summary": result.recommended_next_step,
                    },
                ),
            )
        await session.commit()
    return ScaleScoreResponse(
        scale_type="gad7",
        score=result.score,
        severity=result.severity,
        interpretation=result.interpretation,
        recommended_next_step=result.recommended_next_step,
    )


@router.post("/crisis", response_model=ScaleScoreResponse)
async def submit_crisis(
    payload: CrisisScreenRequest,
    services: Annotated[AppServices, Depends(get_services)],
    request_id: Annotated[str, Depends(get_request_id)],
) -> ScaleScoreResponse:
    result = score_crisis_screen(payload.answers)
    async with services.sessionmaker() as session:
        await _ensure_scope(session, payload.user_id, payload.conversation_id)
        assessment_repo = AssessmentRepository(session)
        risk_repo = RiskRepository(session)
        audit_repo = AuditRepository(session)
        await assessment_repo.save_assessment(
            user_id=payload.user_id,
            conversation_id=payload.conversation_id,
            scale_type="crisis",
            answers=payload.answers,
            score=None,
            severity=result.crisis_level,
            interpretation=result.interpretation,
        )
        await risk_repo.save_risk(
            user_id=payload.user_id,
            conversation_id=payload.conversation_id,
            message_id=None,
            risk=RiskResult(
                crisis_level=result.crisis_level,
                evidence=[{"source": "crisis_screen", "detail": result.interpretation}],
                recommended_next_step={
                    "route": "crisis" if result.safety_response_required else "normal",
                    "summary": result.recommended_next_step,
                },
            ),
        )
        if result.safety_response_required:
            await audit_repo.record_event(
                event_type=SAFETY_ESCALATION_TRIGGERED,
                request_id=request_id,
                user_id=payload.user_id,
                conversation_id=payload.conversation_id,
                payload={"crisis_level": result.crisis_level},
            )
        await session.commit()
    return ScaleScoreResponse(
        scale_type="crisis",
        crisis_level=result.crisis_level,
        interpretation=result.interpretation,
        recommended_next_step=result.recommended_next_step,
    )


async def _ensure_scope(session: Any, user_id: str, conversation_id: str | None) -> None:
    repo = ConversationRepository(session)
    await repo.ensure_user(user_id)
    if conversation_id is not None:
        await repo.ensure_conversation(user_id=user_id, conversation_id=conversation_id)


def cast_depression_risk(value: str) -> DepressionRisk:
    return cast(DepressionRisk, value)


def cast_anxiety_risk(value: str) -> AnxietyRisk:
    return cast(AnxietyRisk, value)
