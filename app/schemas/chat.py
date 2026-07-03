from pydantic import BaseModel, Field

from app.schemas.risk import RiskSummary


class ChatRequest(BaseModel):
    user_id: str
    conversation_id: str
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    message_id: str
    assistant_message: str
    risk_summary: RiskSummary
    suggested_actions: list[str]
    follow_up_questions: list[str]

