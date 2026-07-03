from app.agent.nodes.assessment_node import AssessmentNode
from app.agent.nodes.intent_node import IntentNode
from app.agent.nodes.intervention_node import InterventionNode
from app.agent.nodes.persist_node import PersistNode
from app.agent.nodes.rag_node import RagNode
from app.agent.nodes.response_node import ResponseNode
from app.agent.nodes.risk_node import RiskNode
from app.agent.nodes.safety_node import SafetyNode
from app.agent.nodes.signal_node import SignalExtractionNode
from app.agent.state import AgentState
from app.clinical.llm_signal_extractor import LLMSignalExtractor
from app.llm.base import LLMResponse
from app.llm.prompt_registry import PromptRegistry
from app.observability.audit import AuditLogger
from app.observability.events import LLM_CALL_COMPLETED, LLM_CALL_FAILED


def _state(message: str) -> AgentState:
    return AgentState(
        request_id="req",
        agent_run_id="run",
        user_id="u",
        conversation_id="c",
        user_message=message,
    )


class FakeChatProvider:
    provider = "fake"

    async def chat(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        assert "校园心理支持助手" in system_prompt
        assert "用户消息：你好" in user_prompt
        return LLMResponse(content="你好，我在。今天想先聊点什么？", model="fake", provider="fake")

    async def chat_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        return {}


class FailingSignalProvider:
    async def chat(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        raise RuntimeError("rate limited")

    async def chat_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        raise RuntimeError("rate limited")


class FailingChatProvider:
    async def chat(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:
        raise RuntimeError("rate limited")

    async def chat_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, object]:
        return {}


def test_agent_state_has_node_trace_and_outputs() -> None:
    state = _state("最近睡不着")

    assert state.node_trace == []
    assert state.suggested_actions == []
    assert state.follow_up_questions == []


async def test_safety_node_routes_crisis_message() -> None:
    result = await SafetyNode().run(_state("我不想活了"))

    assert result.route == "crisis"
    assert "safety_node" in result.node_trace


async def test_intent_node_detects_assessment_request() -> None:
    result = await IntentNode().run(_state("我想做 GAD-7"))

    assert result.intent == "assessment"


async def test_assessment_node_keeps_requested_scale_suggestion() -> None:
    state = await IntentNode().run(_state("我想做 PHQ-9"))

    result = await AssessmentNode().run(state)

    assert "PHQ-9" in result.assessment_suggestions


async def test_signal_risk_and_assessment_nodes_fill_state() -> None:
    state = _state("我最近两周考试压力很大，睡不着，注意力下降。")

    state = await SignalExtractionNode().run(state)
    state = await RiskNode().run(state)
    state = await AssessmentNode().run(state)

    assert "焦虑" in state.extracted_signals.emotions
    assert state.risk_result.anxiety_risk == "moderate"
    assert "GAD-7" in state.assessment_suggestions


async def test_signal_node_records_llm_failure_when_provider_fails() -> None:
    audit_logger = AuditLogger()
    llm_extractor = LLMSignalExtractor(
        provider=FailingSignalProvider(),
        prompt_registry=PromptRegistry(),
    )

    result = await SignalExtractionNode(
        llm_signal_extractor=llm_extractor,
        audit_logger=audit_logger,
    ).run(_state("你好"))

    assert result.extracted_signals.emotions == []
    assert any(event["event_type"] == LLM_CALL_FAILED for event in audit_logger.events)
    assert not any(event["event_type"] == LLM_CALL_COMPLETED for event in audit_logger.events)


async def test_rag_node_skips_crisis_route() -> None:
    state = _state("我不想活了")
    state.route = "crisis"

    result = await RagNode().run(state)

    assert result.retrieved_knowledge == []


async def test_intervention_and_response_nodes_generate_outputs() -> None:
    state = _state("我最近两周考试压力很大，睡不着。")
    state = await SignalExtractionNode().run(state)
    state = await RiskNode().run(state)
    state = await InterventionNode().run(state)
    state = await ResponseNode().run(state)

    assert state.suggested_actions
    assert state.response_text
    assert "不是诊断" in state.response_text


async def test_response_node_uses_neutral_fallback_for_greeting_without_signals() -> None:
    result = await ResponseNode().run(_state("你好"))

    assert "可以从一句真实感受开始" in result.response_text
    assert "承受了不少压力" not in result.response_text


async def test_response_node_uses_neutral_fallback_when_llm_fails_without_signals() -> None:
    result = await ResponseNode(llm_provider=FailingChatProvider()).run(_state("你好"))

    assert "可以从一句真实感受开始" in result.response_text
    assert "承受了不少压力" not in result.response_text


async def test_response_node_uses_llm_provider_for_normal_route() -> None:
    result = await ResponseNode(llm_provider=FakeChatProvider()).run(_state("你好"))

    assert result.response_text == "你好，我在。今天想先聊点什么？"


async def test_response_node_keeps_crisis_response_when_llm_provider_is_available() -> None:
    state = _state("我不想活了")
    state.route = "crisis"

    result = await ResponseNode(llm_provider=FakeChatProvider()).run(state)

    assert "请立刻联系" in result.response_text


async def test_persist_node_saves_messages_and_risk(db_session) -> None:
    state = _state("我最近两周考试压力很大，睡不着。")
    state = await SignalExtractionNode().run(state)
    state = await RiskNode().run(state)
    state = await InterventionNode().run(state)
    state = await ResponseNode().run(state)

    result = await PersistNode(session=db_session).run(state)
    await db_session.commit()

    assert result.user_message_id
    assert result.assistant_message_id
