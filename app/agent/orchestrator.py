from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.agent.nodes.assessment_node import AssessmentNode
from app.agent.nodes.intent_node import IntentNode
from app.agent.nodes.intervention_node import InterventionNode
from app.agent.nodes.memory_node import MemoryNode
from app.agent.nodes.persist_node import PersistNode
from app.agent.nodes.rag_node import RagNode
from app.agent.nodes.response_node import ResponseNode
from app.agent.nodes.risk_node import RiskNode
from app.agent.nodes.safety_node import SafetyNode
from app.agent.nodes.signal_node import SignalExtractionNode
from app.agent.pipeline import PipelineRunner
from app.agent.state import AgentState
from app.clinical.llm_signal_extractor import LLMSignalExtractor
from app.clinical.risk_engine import RiskEngine
from app.clinical.signal_extractor import SignalExtractor
from app.core.logging import get_logger
from app.llm.base import LLMProvider
from app.llm.prompt_registry import PromptRegistry
from app.memory.profile_memory import ProfileMemory
from app.observability.audit import AuditLogger
from app.observability.events import (
    AGENT_RUN_COMPLETED,
    AGENT_RUN_STARTED,
    RISK_ASSESSMENT_COMPLETED,
    SAFETY_ESCALATION_TRIGGERED,
)
from app.rag.retriever import KnowledgeRetriever
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.risk import summarize_risk

logger = get_logger("app.agent")


class AgentOrchestrator:
    def __init__(
        self,
        *,
        profile_memory: ProfileMemory,
        retriever: KnowledgeRetriever,
        audit_logger: AuditLogger,
        sessionmaker: async_sessionmaker[AsyncSession] | None = None,
        llm_signal_extractor: LLMSignalExtractor | None = None,
        llm_provider: LLMProvider | None = None,
        prompt_registry: PromptRegistry | None = None,
    ) -> None:
        self.profile_memory = profile_memory
        self.retriever = retriever
        self.audit_logger = audit_logger
        self.sessionmaker = sessionmaker
        self.llm_signal_extractor = llm_signal_extractor
        self.llm_provider = llm_provider
        self.prompt_registry = prompt_registry or PromptRegistry()
        self.extractor = SignalExtractor()
        self.risk_engine = RiskEngine()

    async def handle_chat_state(self, request: ChatRequest, *, request_id: str) -> AgentState:
        agent_run_id = f"run_{uuid4().hex}"
        logger.info(AGENT_RUN_STARTED, request_id=request_id, agent_run_id=agent_run_id)
        state = AgentState(
            request_id=request_id,
            agent_run_id=agent_run_id,
            user_id=request.user_id,
            conversation_id=request.conversation_id,
            user_message=request.message,
        )
        runner = PipelineRunner(
            [
                SafetyNode(),
                MemoryNode(sessionmaker=self.sessionmaker),
                IntentNode(),
                SignalExtractionNode(
                    extractor=self.extractor,
                    llm_signal_extractor=self.llm_signal_extractor,
                    audit_logger=self.audit_logger,
                ),
                RiskNode(risk_engine=self.risk_engine),
                AssessmentNode(),
                RagNode(
                    retriever=self.retriever,
                    sessionmaker=self.sessionmaker,
                    audit_logger=self.audit_logger,
                ),
                InterventionNode(),
                ResponseNode(
                    llm_provider=self.llm_provider,
                    prompt_registry=self.prompt_registry,
                ),
                PersistNode(sessionmaker=self.sessionmaker),
            ]
        )
        state = await runner.run(state)

        if state.route == "crisis":
            self.audit_logger.record_event(
                SAFETY_ESCALATION_TRIGGERED,
                {
                    "request_id": request_id,
                    "agent_run_id": agent_run_id,
                    "user_id": request.user_id,
                    "conversation_id": request.conversation_id,
                    "crisis_level": state.risk_result.crisis_level,
                },
            )
        self.audit_logger.record_event(
            RISK_ASSESSMENT_COMPLETED,
            {
                "request_id": request_id,
                "agent_run_id": agent_run_id,
                "user_id": request.user_id,
                "conversation_id": request.conversation_id,
                "crisis_level": state.risk_result.crisis_level,
                "node_trace": state.node_trace,
            },
        )
        self.profile_memory.update(request.user_id, state.extracted_signals, state.risk_result)
        logger.info(AGENT_RUN_COMPLETED, request_id=request_id, agent_run_id=agent_run_id)
        return state

    async def handle_chat(self, request: ChatRequest, *, request_id: str) -> ChatResponse:
        state = await self.handle_chat_state(request, request_id=request_id)
        return ChatResponse(
            message_id=state.assistant_message_id or f"msg_{uuid4().hex}",
            assistant_message=state.response_text or "",
            risk_summary=summarize_risk(state.risk_result),
            suggested_actions=state.suggested_actions,
            follow_up_questions=state.follow_up_questions,
        )
