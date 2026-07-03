from app.agent.state import AgentState


class AssessmentNode:
    name = "assessment_node"

    async def run(self, state: AgentState) -> AgentState:
        suggestions: list[str] = []
        text = state.user_message
        if state.intent == "assessment":
            if "GAD-7" in text:
                suggestions.append("GAD-7")
            if "PHQ-9" in text:
                suggestions.append("PHQ-9")
            if "危机" in text or "自杀" in text:
                suggestions.append("crisis screen")
        risk = state.risk_result
        if risk.anxiety_risk in {"moderate", "severe"}:
            suggestions.append("GAD-7")
        if risk.depression_risk in {"moderate", "moderately_severe", "severe"}:
            suggestions.append("PHQ-9")
        if risk.crisis_level in {"s1", "s2", "s3", "s4"}:
            suggestions.append("crisis screen")
        state.assessment_suggestions = suggestions
        state.node_trace.append(self.name)
        return state
