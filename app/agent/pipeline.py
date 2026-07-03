from time import perf_counter
from typing import Protocol

from app.agent.state import AgentState, DecisionTraceEntry
from app.core.logging import get_logger
from app.observability.events import AGENT_NODE_COMPLETED, AGENT_NODE_FAILED, AGENT_NODE_STARTED

logger = get_logger("app.agent.pipeline")


class PipelineNode(Protocol):
    name: str

    async def run(self, state: AgentState) -> AgentState:
        pass


class PipelineRunner:
    def __init__(self, nodes: list[PipelineNode]) -> None:
        self.nodes = nodes

    async def run(self, state: AgentState) -> AgentState:
        current = state
        for node in self.nodes:
            before = _state_summary(current)
            started_at = perf_counter()
            logger.info(
                AGENT_NODE_STARTED,
                request_id=current.request_id,
                agent_run_id=current.agent_run_id,
                node=node.name,
            )
            try:
                current = await node.run(current)
            except Exception:
                logger.exception(
                    AGENT_NODE_FAILED,
                    request_id=current.request_id,
                    agent_run_id=current.agent_run_id,
                    node=node.name,
                )
                raise
            latency_ms = round((perf_counter() - started_at) * 1000)
            after = _state_summary(current)
            current.decision_path.append(
                DecisionTraceEntry(
                    step=len(current.decision_path) + 1,
                    node=node.name,
                    latency_ms=latency_ms,
                    before=before,
                    after=after,
                    decision=_describe_decision(node.name, before, after),
                )
            )
            logger.info(
                AGENT_NODE_COMPLETED,
                request_id=current.request_id,
                agent_run_id=current.agent_run_id,
                node=node.name,
            )
        return current


def _state_summary(state: AgentState) -> dict[str, object]:
    risk = state.risk_result
    return {
        "intent": state.intent,
        "route": state.route,
        "crisis_level": risk.crisis_level,
        "anxiety_risk": risk.anxiety_risk,
        "depression_risk": risk.depression_risk,
        "sleep_risk": risk.sleep_risk,
        "risk_markers": list(state.extracted_signals.risk_markers),
        "signal_count": _signal_count(state),
        "retrieved_knowledge_count": len(state.retrieved_knowledge),
        "rag_behavior": state.rag_behavior,
        "response_mode": state.response_mode,
        "suggested_actions_count": len(state.suggested_actions),
        "assessment_suggestions": list(state.assessment_suggestions),
        "llm_signal_status": state.llm_signal_status,
        "llm_response_status": state.llm_response_status,
    }


def _signal_count(state: AgentState) -> int:
    signals = state.extracted_signals
    return sum(
        len(values)
        for values in [
            signals.emotions,
            signals.symptoms,
            signals.stressors,
            signals.function_impairment,
            signals.risk_markers,
            signals.protective_factors,
        ]
    )


def _describe_decision(
    node_name: str,
    before: dict[str, object],
    after: dict[str, object],
) -> str:
    if node_name == "safety_node":
        if before["route"] != after["route"]:
            return "安全预检改变 route，疑似危机表达被预路由"
        return "安全预检未改变 route"
    if node_name == "intent_node":
        return f"意图识别为 {after['intent']}，route 为 {after['route']}"
    if node_name == "signal_node":
        return (
            f"抽取信号数量 {after['signal_count']}，"
            f"LLM 信号状态 {after['llm_signal_status']}"
        )
    if node_name == "risk_node":
        if before["crisis_level"] != after["crisis_level"] or before["route"] != after["route"]:
            return (
                f"风险评估更新为 crisis_level={after['crisis_level']}，"
                f"route={after['route']}"
            )
        return "风险评估未改变危机等级或 route"
    if node_name == "assessment_node":
        suggestions = after["assessment_suggestions"]
        return f"生成筛查建议 {suggestions}" if suggestions else "未生成筛查建议"
    if node_name == "rag_node":
        return f"RAG 行为为 {after['rag_behavior']}"
    if node_name == "intervention_node":
        return f"生成建议动作数量 {after['suggested_actions_count']}"
    if node_name == "response_node":
        return (
            f"回复模式为 {after['response_mode']}，"
            f"LLM 回复状态 {after['llm_response_status']}"
        )
    if node_name == "persist_node":
        return "持久化会话、风险和审计信息"
    return "节点执行完成"
