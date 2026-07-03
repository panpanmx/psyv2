from sqlalchemy import select

from app.db.models import (
    Assessment,
    AuditLog,
    Conversation,
    Message,
    RiskAssessment,
    User,
    UserProfile,
)


def test_models_define_expected_table_names() -> None:
    assert User.__tablename__ == "users"
    assert Conversation.__tablename__ == "conversations"
    assert Message.__tablename__ == "messages"
    assert UserProfile.__tablename__ == "user_profiles"
    assert Assessment.__tablename__ == "assessments"
    assert RiskAssessment.__tablename__ == "risk_assessments"
    assert AuditLog.__tablename__ == "audit_logs"


async def test_models_can_create_related_rows(db_session) -> None:
    user = User(id="u-001", nickname="小安", age_group="undergraduate", school_stage="大一")
    conversation = Conversation(id="c-001", user_id="u-001", title="初次倾诉")
    message = Message(
        id="m-001",
        conversation_id="c-001",
        role="user",
        content="最近睡不着",
        content_hash="hash_001",
        risk_snapshot={"crisis_level": "s0"},
    )
    profile = UserProfile(
        id="p-001",
        user_id="u-001",
        profile_json={"dominant_emotions": ["焦虑"]},
        latest_summary="近期主要情绪：焦虑。",
        risk_trend_json=[],
    )
    assessment = Assessment(
        id="a-001",
        user_id="u-001",
        conversation_id="c-001",
        scale_type="gad7",
        answers=[1, 1, 1, 1, 1, 0, 0],
        score=5,
        severity="mild",
        interpretation="轻度焦虑风险",
    )
    risk = RiskAssessment(
        id="r-001",
        user_id="u-001",
        conversation_id="c-001",
        message_id="m-001",
        anxiety_risk="mild",
        crisis_level="s0",
        evidence=[{"source": "message", "detail": "睡眠困难"}],
        recommended_next_step={"route": "normal"},
    )
    audit = AuditLog(
        id="audit-001",
        request_id="req-001",
        user_id="u-001",
        conversation_id="c-001",
        event_type="risk.assessment.completed",
        event_payload={"crisis_level": "s0"},
    )

    db_session.add_all([user, conversation, message, profile, assessment, risk, audit])
    await db_session.commit()

    result = await db_session.execute(select(Message).where(Message.id == "m-001"))
    saved = result.scalar_one()
    assert saved.content_hash == "hash_001"
    assert saved.risk_snapshot["crisis_level"] == "s0"
