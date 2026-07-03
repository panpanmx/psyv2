from app.clinical.interventions.behavioral_activation import behavioral_activation_actions
from app.clinical.interventions.cbt import anxiety_cbt_actions, depression_cbt_actions
from app.clinical.interventions.mindfulness import mindfulness_actions
from app.clinical.interventions.referral import referral_actions
from app.clinical.interventions.sleep_hygiene import sleep_actions
from app.schemas.risk import RiskResult


def select_interventions(risk: RiskResult) -> list[str]:
    if risk.crisis_level in {"s2", "s3", "s4"}:
        return referral_actions()

    actions: list[str] = []
    if risk.anxiety_risk in {"mild", "moderate", "severe"}:
        actions.extend(anxiety_cbt_actions())
        actions.extend(mindfulness_actions()[:1])
    if risk.depression_risk in {"mild", "moderate", "moderately_severe", "severe"}:
        actions.extend(behavioral_activation_actions())
        actions.extend(depression_cbt_actions())
    if risk.sleep_risk in {"mild", "moderate", "severe"}:
        actions.extend(sleep_actions())
    if not actions:
        actions.append("记录今天情绪变化，并观察睡眠、食欲和学习状态")
    return list(dict.fromkeys(actions))

