from app.agent.state import AgentState


class IntentNode:
    name = "intent_node"

    async def run(self, state: AgentState) -> AgentState:
        text = state.user_message
        if state.route == "crisis":
            state.intent = "crisis"
        elif any(token in text for token in ["GAD-7", "PHQ-9", "量表", "筛查"]):
            state.intent = "assessment"
            state.route = "assessment"
        else:
            state.intent = "support"
        state.node_trace.append(self.name)
        return state
