from typing import Literal

from pydantic import BaseModel, Field

CrisisLevel = Literal["s0", "s1", "s2", "s3", "s4"]
DepressionRisk = Literal["none", "mild", "moderate", "moderately_severe", "severe", "unknown"]
AnxietyRisk = Literal["none", "mild", "moderate", "severe", "unknown"]
GenericRisk = Literal["none", "mild", "moderate", "severe", "unknown"]


class ExtractedSignals(BaseModel):
    emotions: list[str] = Field(default_factory=list)
    symptoms: list[str] = Field(default_factory=list)
    duration: str | None = None
    frequency: str | None = None
    stressors: list[str] = Field(default_factory=list)
    function_impairment: list[str] = Field(default_factory=list)
    risk_markers: list[str] = Field(default_factory=list)
    protective_factors: list[str] = Field(default_factory=list)


class RiskResult(BaseModel):
    depression_risk: DepressionRisk = "unknown"
    anxiety_risk: AnxietyRisk = "unknown"
    sleep_risk: GenericRisk = "unknown"
    crisis_level: CrisisLevel = "s0"
    function_impairment_level: GenericRisk = "unknown"
    evidence: list[dict[str, str]] = Field(default_factory=list)
    recommended_next_step: dict[str, str] = Field(default_factory=dict)


class RiskSummary(BaseModel):
    depression_risk: DepressionRisk
    anxiety_risk: AnxietyRisk
    sleep_risk: GenericRisk
    crisis_level: CrisisLevel
    function_impairment_level: GenericRisk


def summarize_risk(result: RiskResult) -> RiskSummary:
    return RiskSummary(
        depression_risk=result.depression_risk,
        anxiety_risk=result.anxiety_risk,
        sleep_risk=result.sleep_risk,
        crisis_level=result.crisis_level,
        function_impairment_level=result.function_impairment_level,
    )

