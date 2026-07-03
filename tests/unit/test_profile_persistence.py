from app.clinical.risk_engine import RiskEngine
from app.clinical.signal_extractor import SignalExtractor
from app.db.repositories.conversation_repo import ConversationRepository
from app.db.repositories.profile_repo import ProfileRepository


async def test_profile_repo_updates_profile_and_risk_timeline(db_session) -> None:
    conversation_repo = ConversationRepository(db_session)
    await conversation_repo.ensure_user("u-profile")

    signals = SignalExtractor().extract("最近两周很低落，也不想见同学，但愿意找朋友聊聊。")
    risk = RiskEngine().assess(signals=signals)

    repo = ProfileRepository(db_session)
    await repo.update_profile(user_id="u-profile", signals=signals, risk=risk, message_id="msg_001")
    await db_session.commit()

    profile = await repo.get_profile("u-profile")
    timeline = await repo.get_timeline("u-profile")

    assert "低落" in profile["dominant_emotions"]
    assert "朋友支持" in profile["protective_factors"]
    assert timeline[-1]["depression_risk"] == "moderate"
