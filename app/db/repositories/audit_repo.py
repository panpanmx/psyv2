from typing import Any
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLog


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_event(
        self,
        *,
        event_type: str,
        request_id: str,
        user_id: str | None,
        conversation_id: str | None,
        payload: dict[str, Any],
    ) -> AuditLog:
        row = AuditLog(
            id=f"audit_{uuid4().hex}",
            request_id=request_id,
            user_id=user_id,
            conversation_id=conversation_id,
            event_type=event_type,
            event_payload=payload,
        )
        self.session.add(row)
        await self.session.flush()
        return row
