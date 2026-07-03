from collections.abc import AsyncIterator
from typing import cast

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.services import AppServices


def get_services(request: Request) -> AppServices:
    return cast(AppServices, request.app.state.services)


def get_request_id(request: Request) -> str:
    return str(getattr(request.state, "request_id", "req_unknown"))


async def get_db_session(request: Request) -> AsyncIterator[AsyncSession]:
    services = get_services(request)
    async with services.sessionmaker() as session:
        yield session
