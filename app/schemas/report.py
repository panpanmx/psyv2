from pydantic import BaseModel

from app.schemas.risk import RiskSummary


class ReportResponse(BaseModel):
    user_id: str
    profile_summary: str
    risk_summary: RiskSummary
    evidence_summary: list[str]
    recommended_interventions: list[str]
    offline_help_recommended: bool

