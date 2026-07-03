from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agent.state import AgentState
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.conversation_repo import content_hash
from app.db.repositories.knowledge_repo import KnowledgeRepository
from app.observability.audit import AuditLogger
from app.observability.events import RAG_RETRIEVE_COMPLETED
from app.rag.retriever import KnowledgeRetriever


class RagNode:
    name = "rag_node"

    def __init__(
        self,
        *,
        retriever: KnowledgeRetriever | None = None,
        sessionmaker: async_sessionmaker[AsyncSession] | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self.retriever = retriever or KnowledgeRetriever()
        self.sessionmaker = sessionmaker
        self.audit_logger = audit_logger

    async def run(self, state: AgentState) -> AgentState:
        if state.route == "crisis":
            state.retrieved_knowledge = []
            state.rag_behavior = "skip"
            state.node_trace.append(self.name)
            return state
        if self.sessionmaker is None:
            state.retrieved_knowledge = await self.retriever.retrieve_async(state.user_message)
            state.rag_behavior = "used" if state.retrieved_knowledge else "empty"
            self._audit_memory(state)
            state.node_trace.append(self.name)
            return state
        async with self.sessionmaker() as session:
            repository = KnowledgeRepository(session)
            state.retrieved_knowledge = await self.retriever.retrieve_async(
                state.user_message,
                repository=repository,
            )
            state.rag_behavior = "used" if state.retrieved_knowledge else "empty"
            await AuditRepository(session).record_event(
                event_type=RAG_RETRIEVE_COMPLETED,
                request_id=state.request_id,
                user_id=state.user_id,
                conversation_id=state.conversation_id,
                payload=_payload(state),
            )
            await session.commit()
        self._audit_memory(state)
        state.node_trace.append(self.name)
        return state

    def _audit_memory(self, state: AgentState) -> None:
        if self.audit_logger is None:
            return
        self.audit_logger.record_event(
            RAG_RETRIEVE_COMPLETED,
            {
                "request_id": state.request_id,
                "user_id": state.user_id,
                "conversation_id": state.conversation_id,
                **_payload(state),
            },
        )


def _payload(state: AgentState) -> dict[str, object]:
    return {
        "agent_run_id": state.agent_run_id,
        "query_hash": content_hash(state.user_message),
        "top_k": len(state.retrieved_knowledge),
        "chunk_ids": [
            item.get("chunk_id", item.get("id", "")) for item in state.retrieved_knowledge
        ],
        "scores": [item.get("score", "0") for item in state.retrieved_knowledge],
    }
