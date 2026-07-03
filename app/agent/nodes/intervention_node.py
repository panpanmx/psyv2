from app.agent.state import AgentState
from app.clinical.interventions import select_interventions


class InterventionNode:
    name = "intervention_node"

    async def run(self, state: AgentState) -> AgentState:
        actions = select_interventions(state.risk_result)
        if _is_contact_help_seeking(state.user_message):
            contact_action = "联系学校心理中心或可信任老师"
            if contact_action not in actions:
                actions.append(contact_action)
        for suggestion in state.assessment_suggestions:
            if suggestion not in actions:
                actions.append(suggestion)
            action = f"建议完成 {suggestion} 进一步筛查"
            if action not in actions:
                actions.append(action)
        state.suggested_actions = actions
        state.intervention_plan = {"actions": actions}
        state.node_trace.append(self.name)
        return state


def _is_contact_help_seeking(message: str) -> bool:
    return "联系" in message and any(token in message for token in ["心理中心", "辅导员", "老师"])
