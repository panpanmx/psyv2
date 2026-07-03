from app.agent.state import AgentState
from app.clinical.signal_extractor import SignalExtractor


class SafetyNode:
    name = "safety_node"

    def __init__(self, *, extractor: SignalExtractor | None = None) -> None:
        self.extractor = extractor or SignalExtractor()

    async def run(self, state: AgentState) -> AgentState:
        signals = self.extractor.extract(state.user_message)
        if "主动自杀想法" in signals.risk_markers:
            state.route = "crisis"
        state.node_trace.append(self.name)
        return state
