from sqlalchemy import select

from app.clinical.risk_engine import RiskEngine
from app.clinical.signal_extractor import SignalExtractor
from app.db.models import AuditLog, RiskAssessment
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.conversation_repo import ConversationRepository
from app.db.repositories.risk_repo import RiskRepository


async def test_risk_repo_persists_evidence_and_next_step(db_session) -> None:
    conversation_repo = ConversationRepository(db_session)
    await conversation_repo.ensure_user("u-risk")
    await conversation_repo.ensure_conversation("u-risk", "c-risk")

    signals = SignalExtractor().extract("我不想活了，已经想好了方式。")
    risk = RiskEngine().assess(signals=signals)

    repo = RiskRepository(db_session)
    saved = await repo.save_risk(
        user_id="u-risk",
        conversation_id="c-risk",
        message_id="msg-risk",
        risk=risk,
    )
    await db_session.commit()

    result = await db_session.execute(select(RiskAssessment).where(RiskAssessment.id == saved.id))
    row = result.scalar_one()
    assert row.crisis_level == "s3"
    assert row.recommended_next_step["route"] == "crisis"


async def test_audit_repo_persists_safety_escalation(db_session) -> None:
    repo = AuditRepository(db_session)
    await repo.record_event(
        event_type="safety.escalation.triggered",
        request_id="req_001",
        user_id="u-risk",
        conversation_id="c-risk",
        payload={"crisis_level": "s3"},
    )
    await db_session.commit()

    result = await db_session.execute(select(AuditLog))
    row = result.scalar_one()
    assert row.event_type == "safety.escalation.triggered"
    assert row.event_payload["crisis_level"] == "s3"
