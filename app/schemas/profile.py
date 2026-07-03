from pydantic import BaseModel, Field


class UserProfileResponse(BaseModel):
    user_id: str
    profile: dict[str, list[str]] = Field(default_factory=dict)
    latest_summary: str


class ProfileTimelineResponse(BaseModel):
    user_id: str
    risk_timeline: list[dict[str, str]]
