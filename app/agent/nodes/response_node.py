from app.agent.state import AgentState
from app.clinical.policies.safety_policy import crisis_response
from app.core.logging import get_logger
from app.llm.base import LLMProvider
from app.llm.local_provider import LocalProvider
from app.llm.prompt_registry import PromptRegistry
from app.observability.events import LLM_CALL_COMPLETED, LLM_CALL_FAILED, LLM_CALL_STARTED

logger = get_logger("app.agent.response_node")


class ResponseNode:
    name = "response_node"

    def __init__(
        self,
        *,
        llm_provider: LLMProvider | None = None,
        prompt_registry: PromptRegistry | None = None,
    ) -> None:
        self.llm_provider = llm_provider
        self.prompt_registry = prompt_registry or PromptRegistry()

    async def run(self, state: AgentState) -> AgentState:
        if state.route == "crisis":
            state.response_mode = "crisis_template"
            state.llm_response_status = "skipped_crisis_template"
            state.response_text = crisis_response()
            state.follow_up_questions = ["你现在身边是否有可信任的人可以马上陪你？"]
        else:
            state.response_mode = (
                "assessment_prompt" if state.route == "assessment" else "normal_support"
            )
            state.follow_up_questions = _follow_up_questions(state)
            state.response_text = await self._normal_response(state)
        state.node_trace.append(self.name)
        return state

    async def _normal_response(self, state: AgentState) -> str:
        fallback = _normal_response(state)
        if self.llm_provider is None or isinstance(self.llm_provider, LocalProvider):
            state.llm_response_status = "fallback_local"
            return fallback

        logger.info(
            LLM_CALL_STARTED,
            request_id=state.request_id,
            agent_run_id=state.agent_run_id,
            node=self.name,
        )
        try:
            result = await self.llm_provider.chat(
                system_prompt=self.prompt_registry.get("response_generation_v1"),
                user_prompt=_response_user_prompt(state),
            )
        except Exception:
            state.llm_response_status = "failed_fallback"
            logger.warning(
                LLM_CALL_FAILED,
                request_id=state.request_id,
                agent_run_id=state.agent_run_id,
                node=self.name,
            )
            return fallback

        content = result.content.strip()
        state.llm_response_status = "completed"
        logger.info(
            LLM_CALL_COMPLETED,
            request_id=state.request_id,
            agent_run_id=state.agent_run_id,
            node=self.name,
        )
        return content or fallback


def _normal_response(state: AgentState) -> str:
    if not _has_support_signals(state):
        return (
            "你好，我在。你可以从一句真实感受开始，"
            "也可以直接说最近最困扰你的学习、睡眠或情绪问题。"
        )

    risk = state.risk_result
    observed: list[str] = []
    if risk.anxiety_risk in {"mild", "moderate", "severe"}:
        observed.append("焦虑或压力相关信号")
    if risk.depression_risk in {"mild", "moderate", "moderately_severe", "severe"}:
        observed.append("低落或抑郁相关信号")
    if risk.sleep_risk in {"mild", "moderate", "severe"}:
        observed.append("睡眠受影响")
    observed_text = "、".join(observed) or "近期压力信号"
    knowledge = state.retrieved_knowledge
    knowledge_hint = f"我会参考{knowledge[0]['title']}里的方法。" if knowledge else ""
    action = state.suggested_actions[0] if state.suggested_actions else "记录今天的情绪变化"
    return (
        "听起来你最近确实承受了不少压力，这种状态值得被认真对待。"
        f"从你的描述看，我观察到{observed_text}，这不是诊断，但提示可以进一步筛查和照顾自己。"
        f"{knowledge_hint} 现在可以先做一个很小的稳定动作：{action}。"
        "如果这些状态持续加重，建议联系学校心理中心或专业人员进一步评估。"
    )


def _has_support_signals(state: AgentState) -> bool:
    signals = state.extracted_signals
    return any(
        [
            signals.emotions,
            signals.symptoms,
            signals.stressors,
            signals.function_impairment,
            signals.risk_markers,
            state.risk_result.evidence,
            state.retrieved_knowledge,
            state.assessment_suggestions,
        ]
    )


def _response_user_prompt(state: AgentState) -> str:
    risk = state.risk_result
    knowledge_lines = [
        f"- {item.get('title', '知识库片段')}: {item.get('content', '')[:120]}"
        for item in state.retrieved_knowledge[:2]
    ]
    actions = "；".join(state.suggested_actions[:3]) or "暂无"
    follow_ups = "；".join(state.follow_up_questions[:2]) or "暂无"
    knowledge = "\n".join(knowledge_lines) or "暂无"
    return (
        f"用户消息：{state.user_message}\n"
        "风险摘要："
        f"焦虑={risk.anxiety_risk}，抑郁={risk.depression_risk}，睡眠={risk.sleep_risk}，"
        f"危机={risk.crisis_level}，功能受损={risk.function_impairment_level}\n"
        f"建议行动：{actions}\n"
        f"可用追问：{follow_ups}\n"
        f"知识库要点：\n{knowledge}"
    )


def _follow_up_questions(state: AgentState) -> list[str]:
    risk = state.risk_result
    if risk.sleep_risk in {"mild", "moderate", "severe"}:
        return ["这种睡不着大概持续多久了？"]
    if risk.depression_risk in {"mild", "moderate", "moderately_severe", "severe"}:
        return ["这种低落最明显是在一天里的什么时候？"]
    return ["这件事最近对你的学习或生活影响最大的是哪一部分？"]
