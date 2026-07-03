from hashlib import sha256
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Conversation, Message, User


class ConversationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ensure_user(
        self,
        user_id: str,
        *,
        nickname: str = "",
        age_group: str = "unknown",
        school_stage: str = "",
    ) -> User:
        existing = await self.session.get(User, user_id)
        if existing is not None:
            return existing
        user = User(
            id=user_id,
            nickname=nickname,
            age_group=age_group,
            school_stage=school_stage,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def ensure_conversation(
        self,
        user_id: str,
        conversation_id: str,
        *,
        title: str = "心理支持对话",
    ) -> Conversation:
        await self.ensure_user(user_id)
        existing = await self.session.get(Conversation, conversation_id)
        if existing is not None:
            return existing
        conversation = Conversation(id=conversation_id, user_id=user_id, title=title)
        self.session.add(conversation)
        await self.session.flush()
        return conversation

    async def save_message(
        self,
        *,
        conversation_id: str,
        role: str,
        content: str,
        risk_snapshot: dict[str, object],
    ) -> Message:
        message = Message(
            id=f"msg_{uuid4().hex}",
            conversation_id=conversation_id,
            role=role,
            content=content,
            content_hash=content_hash(content),
            risk_snapshot=risk_snapshot,
        )
        self.session.add(message)
        await self.session.flush()
        return message

    async def recent_messages(self, conversation_id: str, *, limit: int = 10) -> list[Message]:
        result = await self.session.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars())


def content_hash(content: str) -> str:
    return sha256(content.encode("utf-8")).hexdigest()

