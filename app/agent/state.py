from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.risk import ExtractedSignals, RiskResult


class DecisionTraceEntry(BaseModel):
    step: int
    node: str
    latency_ms: int
    before: dict[str, Any]
    after: dict[str, Any]
    decision: str


class AgentState(BaseModel):
    request_id: str
    agent_run_id: str
    user_id: str
    conversation_id: str
    user_message: str
    intent: str | None = None
    recent_messages: list[dict[str, Any]] = Field(default_factory=list)
    profile: dict[str, Any] = Field(default_factory=dict)
    extracted_signals: ExtractedSignals = Field(default_factory=ExtractedSignals)
    risk_result: RiskResult = Field(default_factory=RiskResult)
    retrieved_knowledge: list[dict[str, Any]] = Field(default_factory=list)
    intervention_plan: dict[str, Any] = Field(default_factory=dict)
    response_text: str | None = None
    route: Literal["normal", "assessment", "crisis"] = "normal"
    node_trace: list[str] = Field(default_factory=list)
    decision_path: list[DecisionTraceEntry] = Field(default_factory=list)
    suggested_actions: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)
    assistant_message_id: str | None = None
    user_message_id: str | None = None
    assessment_suggestions: list[str] = Field(default_factory=list)
    rag_behavior: Literal["not_run", "used", "empty", "skip"] = "not_run"
    response_mode: Literal[
        "not_run",
        "normal_support",
        "assessment_prompt",
        "crisis_template",
    ] = "not_run"
    llm_signal_status: Literal["not_run", "not_configured", "completed", "failed"] = "not_run"
    llm_response_status: Literal[
        "not_run",
        "skipped_crisis_template",
        "fallback_local",
        "completed",
        "failed_fallback",
    ] = "not_run"
