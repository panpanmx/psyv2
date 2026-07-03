from typing import Any, Literal

from pydantic import BaseModel, Field


class CrisisScreenResult(BaseModel):
    crisis_level: Literal["s0", "s1", "s2", "s3", "s4"]
    immediacy: Literal["none", "recent", "current"]
    protective_factors: list[str] = Field(default_factory=list)
    safety_response_required: bool
    interpretation: str
    recommended_next_step: str


def score_crisis_screen(answers: dict[str, Any]) -> CrisisScreenResult:
    passive = bool(answers.get("passive_ideation"))
    active = bool(answers.get("active_ideation"))
    method = bool(answers.get("method"))
    plan = bool(answers.get("plan"))
    intent = bool(answers.get("intent"))
    preparation = bool(answers.get("preparation"))
    recent_attempt = bool(answers.get("recent_attempt"))
    protective = list(answers.get("protective_factors") or [])

    if recent_attempt or (active and plan and intent and preparation):
        level: Literal["s0", "s1", "s2", "s3", "s4"] = "s4"
    elif active and (plan or intent or preparation):
        level = "s3"
    elif active or method:
        level = "s2"
    elif passive:
        level = "s1"
    else:
        level = "s0"

    immediacy: Literal["none", "recent", "current"]
    if level in {"s3", "s4"}:
        immediacy = "current"
    elif level in {"s1", "s2"}:
        immediacy = "recent"
    else:
        immediacy = "none"

    safety_required = level in {"s2", "s3", "s4"}
    next_step = (
        "请立刻联系可信成年人、学校心理中心或当地紧急援助。"
        if safety_required
        else "建议继续观察，并在风险想法增强时主动求助。"
    )
    return CrisisScreenResult(
        crisis_level=level,
        immediacy=immediacy,
        protective_factors=protective,
        safety_response_required=safety_required,
        interpretation=f"简化危机筛查提示 {level} 级风险。",
        recommended_next_step=next_step,
    )

