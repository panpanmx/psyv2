from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agent.state import AgentState
from app.db.repositories.conversation_repo import ConversationRepository
from app.db.repositories.profile_repo import ProfileRepository


class MemoryNode:
    name = "memory_node"

    def __init__(
        self,
        *,
        sessionmaker: async_sessionmaker[AsyncSession] | None = None,
        recent_limit: int = 10,
    ) -> None:
        self.sessionmaker = sessionmaker
        self.recent_limit = recent_limit

    async def run(self, state: AgentState) -> AgentState:
        if self.sessionmaker is None:
            state.node_trace.append(self.name)
            return state
        async with self.sessionmaker() as session:
            conversation_repo = ConversationRepository(session)
            profile_repo = ProfileRepository(session)
            messages = await conversation_repo.recent_messages(
                state.conversation_id,
                limit=self.recent_limit,
            )
            state.recent_messages = [
                {"role": message.role, "content": message.content} for message in reversed(messages)
            ]
            try:
                state.profile = await profile_repo.get_profile(state.user_id)
            except Exception:
                state.profile = {}
        state.node_trace.append(self.name)
        return state
