from app.agent.state import AgentState
from app.clinical.llm_signal_extractor import LLMSignalExtractor, merge_signals_safely
from app.clinical.signal_extractor import SignalExtractor
from app.core.logging import get_logger
from app.observability.audit import AuditLogger
from app.observability.events import LLM_CALL_COMPLETED, LLM_CALL_FAILED, LLM_CALL_STARTED
from app.schemas.risk import ExtractedSignals

logger = get_logger("app.agent.signal_node")


class SignalExtractionNode:
    name = "signal_node"

    def __init__(
        self,
        *,
        extractor: SignalExtractor | None = None,
        llm_signal_extractor: LLMSignalExtractor | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self.extractor = extractor or SignalExtractor()
        self.llm_signal_extractor = llm_signal_extractor
        self.audit_logger = audit_logger

    async def run(self, state: AgentState) -> AgentState:
        rule_signals = self.extractor.extract(state.user_message)
        llm_signals = await self._extract_llm(state)
        state.extracted_signals = merge_signals_safely(rule_signals, llm_signals)
        state.node_trace.append(self.name)
        return state

    async def _extract_llm(self, state: AgentState) -> ExtractedSignals:
        if self.llm_signal_extractor is None:
            state.llm_signal_status = "not_configured"
            return ExtractedSignals()
        logger.info(LLM_CALL_STARTED, request_id=state.request_id, agent_run_id=state.agent_run_id)
        try:
            signals = await self.llm_signal_extractor.extract(state.user_message)
            if self.llm_signal_extractor.last_error is not None:
                state.llm_signal_status = "failed"
                error_type = type(self.llm_signal_extractor.last_error).__name__
                logger.warning(
                    LLM_CALL_FAILED,
                    request_id=state.request_id,
                    agent_run_id=state.agent_run_id,
                    node=self.name,
                    error_type=error_type,
                )
                if self.audit_logger is not None:
                    self.audit_logger.record_event(
                        LLM_CALL_FAILED,
                        {
                            "request_id": state.request_id,
                            "agent_run_id": state.agent_run_id,
                            "user_id": state.user_id,
                            "conversation_id": state.conversation_id,
                            "node": self.name,
                            "error_type": error_type,
                        },
                )
                return signals
            state.llm_signal_status = "completed"
            logger.info(
                LLM_CALL_COMPLETED,
                request_id=state.request_id,
                agent_run_id=state.agent_run_id,
                node=self.name,
            )
            if self.audit_logger is not None:
                self.audit_logger.record_event(
                    LLM_CALL_COMPLETED,
                    {
                        "request_id": state.request_id,
                        "agent_run_id": state.agent_run_id,
                        "user_id": state.user_id,
                        "conversation_id": state.conversation_id,
                        "node": self.name,
                        "fields": sorted(signals.model_fields_set),
                    },
            )
            return signals
        except Exception:
            state.llm_signal_status = "failed"
            logger.warning(
                LLM_CALL_FAILED,
                request_id=state.request_id,
                agent_run_id=state.agent_run_id,
                node=self.name,
            )
            return ExtractedSignals()
