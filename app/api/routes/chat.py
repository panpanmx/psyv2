from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_request_id, get_services
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import AppServices

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/messages", response_model=ChatResponse)
async def create_message(
    payload: ChatRequest,
    services: Annotated[AppServices, Depends(get_services)],
    request_id: Annotated[str, Depends(get_request_id)],
) -> ChatResponse:
    return await services.agent.handle_chat(payload, request_id=request_id)
