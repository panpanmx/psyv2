from app.agent.pipeline import PipelineRunner
from app.agent.state import AgentState


class DemoNode:
    name = "demo"

    async def run(self, state: AgentState) -> AgentState:
        state.route = "assessment"
        state.intent = "assessment"
        state.node_trace.append(self.name)
        return state


async def test_pipeline_runner_executes_nodes_in_order() -> None:
    state = AgentState(
        request_id="req",
        agent_run_id="run",
        user_id="u",
        conversation_id="c",
        user_message="hi",
    )
    result = await PipelineRunner([DemoNode(), DemoNode()]).run(state)

    assert result.node_trace == ["demo", "demo"]


async def test_pipeline_runner_records_decision_path_for_each_node() -> None:
    state = AgentState(
        request_id="req",
        agent_run_id="run",
        user_id="u",
        conversation_id="c",
        user_message="hi",
    )

    result = await PipelineRunner([DemoNode()]).run(state)

    assert len(result.decision_path) == 1
    entry = result.decision_path[0]
    assert entry.step == 1
    assert entry.node == "demo"
    assert entry.latency_ms >= 0
    assert entry.before["route"] == "normal"
    assert entry.after["route"] == "assessment"
    assert entry.after["intent"] == "assessment"
    assert entry.decision
