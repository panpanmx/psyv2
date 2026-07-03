from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import get_services
from app.db.repositories.profile_repo import ProfileRepository
from app.schemas.profile import ProfileTimelineResponse, UserProfileResponse
from app.services import AppServices

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_profile(
    user_id: str,
    services: Annotated[AppServices, Depends(get_services)],
) -> UserProfileResponse:
    async with services.sessionmaker() as session:
        repo = ProfileRepository(session)
        profile = await repo.get_profile(user_id)
        summary = await repo.get_summary(user_id)
    return UserProfileResponse(
        user_id=user_id,
        profile=profile,
        latest_summary=summary,
    )


@router.get("/{user_id}/timeline", response_model=ProfileTimelineResponse)
async def get_timeline(
    user_id: str,
    services: Annotated[AppServices, Depends(get_services)],
) -> ProfileTimelineResponse:
    async with services.sessionmaker() as session:
        repo = ProfileRepository(session)
        timeline = await repo.get_timeline(user_id)
    return ProfileTimelineResponse(
        user_id=user_id,
        risk_timeline=timeline,
    )
