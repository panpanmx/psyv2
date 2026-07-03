from typing import Literal

from pydantic import BaseModel, Field


class ScaleScoreResponse(BaseModel):
    scale_type: Literal["phq9", "gad7", "crisis"]
    score: int | None = None
    severity: str | None = None
    crisis_level: str | None = None
    interpretation: str
    recommended_next_step: str


class ScaleAnswersRequest(BaseModel):
    user_id: str
    conversation_id: str | None = None
    answers: list[int] = Field(default_factory=list)


class CrisisScreenRequest(BaseModel):
    user_id: str
    conversation_id: str | None = None
    answers: dict[str, bool | list[str]]

