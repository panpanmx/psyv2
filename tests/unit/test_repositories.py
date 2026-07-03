from sqlalchemy import select

from app.db.models import Message
from app.db.repositories.conversation_repo import ConversationRepository


async def test_conversation_repo_creates_user_conversation_and_messages(db_session) -> None:
    repo = ConversationRepository(db_session)

    await repo.ensure_user(user_id="u-001")
    await repo.ensure_conversation(user_id="u-001", conversation_id="c-001")
    user_message = await repo.save_message(
        conversation_id="c-001",
        role="user",
        content="我最近睡不着",
        risk_snapshot={"crisis_level": "s0"},
    )
    assistant_message = await repo.save_message(
        conversation_id="c-001",
        role="assistant",
        content="听起来你最近很辛苦。",
        risk_snapshot={"crisis_level": "s0"},
    )
    await db_session.commit()

    assert user_message.content_hash != assistant_message.content_hash
    result = await db_session.execute(select(Message).order_by(Message.created_at))
    messages = list(result.scalars())
    assert [message.role for message in messages] == ["user", "assistant"]
    assert messages[0].content_hash
