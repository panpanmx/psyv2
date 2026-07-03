from pathlib import Path
from typing import Any

from app.core.logging import get_logger
from app.db.repositories.audit_repo import AuditRepository

logger = get_logger("app.audit")


class AuditLogger:
    def __init__(self, path: str = "logs/audit.jsonl") -> None:
        self.path = Path(path)
        self.events: list[dict[str, Any]] = []

    def record_event(self, event_type: str, payload: dict[str, Any]) -> None:
        event = {"event_type": event_type, "payload": payload}
        self.events.append(event)
        logger.info(event_type, **payload)

    async def async_record_event(
        self,
        *,
        event_type: str,
        request_id: str,
        user_id: str | None,
        conversation_id: str | None,
        payload: dict[str, Any],
        repository: AuditRepository,
    ) -> None:
        self.record_event(event_type, payload | {"request_id": request_id})
        await repository.record_event(
            event_type=event_type,
            request_id=request_id,
            user_id=user_id,
            conversation_id=conversation_id,
            payload=payload,
        )
