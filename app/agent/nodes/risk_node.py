from app.agent.state import AgentState
from app.clinical.risk_engine import RiskEngine


class RiskNode:
    name = "risk_node"

    def __init__(self, *, risk_engine: RiskEngine | None = None) -> None:
        self.risk_engine = risk_engine or RiskEngine()

    async def run(self, state: AgentState) -> AgentState:
        state.risk_result = self.risk_engine.assess(signals=state.extracted_signals)
        if state.risk_result.crisis_level in {"s2", "s3", "s4"}:
            state.route = "crisis"
        state.node_trace.append(self.name)
        return state
