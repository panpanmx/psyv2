from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agent.state import AgentState
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.conversation_repo import ConversationRepository
from app.db.repositories.profile_repo import ProfileRepository
from app.db.repositories.risk_repo import RiskRepository
from app.observability.events import RISK_ASSESSMENT_COMPLETED, SAFETY_ESCALATION_TRIGGERED
from app.schemas.risk import summarize_risk


class PersistNode:
    name = "persist_node"

    def __init__(
        self,
        *,
        session: AsyncSession | None = None,
        sessionmaker: async_sessionmaker[AsyncSession] | None = None,
    ) -> None:
        self.session = session
        self.sessionmaker = sessionmaker

    async def run(self, state: AgentState) -> AgentState:
        if self.session is not None:
            await self._persist(state, self.session)
        elif self.sessionmaker is not None:
            async with self.sessionmaker() as session:
                await self._persist(state, session)
                await session.commit()
        state.node_trace.append(self.name)
        return state

    async def _persist(self, state: AgentState, session: AsyncSession) -> None:
        conversation_repo = ConversationRepository(session)
        risk_repo = RiskRepository(session)
        profile_repo = ProfileRepository(session)
        audit_repo = AuditRepository(session)
        await conversation_repo.ensure_conversation(
            user_id=state.user_id,
            conversation_id=state.conversation_id,
        )
        user_message = await conversation_repo.save_message(
            conversation_id=state.conversation_id,
            role="user",
            content=state.user_message,
            risk_snapshot=summarize_risk(state.risk_result).model_dump(),
        )
        state.user_message_id = user_message.id
        await risk_repo.save_risk(
            user_id=state.user_id,
            conversation_id=state.conversation_id,
            message_id=user_message.id,
            risk=state.risk_result,
        )
        assistant = await conversation_repo.save_message(
            conversation_id=state.conversation_id,
            role="assistant",
            content=state.response_text or "",
            risk_snapshot=summarize_risk(state.risk_result).model_dump(),
        )
        state.assistant_message_id = assistant.id
        await profile_repo.update_profile(
            user_id=state.user_id,
            signals=state.extracted_signals,
            risk=state.risk_result,
            message_id=user_message.id,
        )
        await audit_repo.record_event(
            event_type=RISK_ASSESSMENT_COMPLETED,
            request_id=state.request_id,
            user_id=state.user_id,
            conversation_id=state.conversation_id,
            payload={
                "agent_run_id": state.agent_run_id,
                "crisis_level": state.risk_result.crisis_level,
                "node_trace": state.node_trace,
            },
        )
        if state.route == "crisis":
            await audit_repo.record_event(
                event_type=SAFETY_ESCALATION_TRIGGERED,
                request_id=state.request_id,
                user_id=state.user_id,
                conversation_id=state.conversation_id,
                payload={
                    "agent_run_id": state.agent_run_id,
                    "crisis_level": state.risk_result.crisis_level,
                },
            )
        await session.flush()
