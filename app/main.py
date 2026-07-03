from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import assessment, chat, health, profile, report
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RequestIdMiddleware
from app.db import models as _models
from app.db.base import Base
from app.db.session import create_engine, create_sessionmaker
from app.services import AppServices

_ = _models


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    engine = create_engine(settings)
    sessionmaker = create_sessionmaker(engine)
    static_dir = Path(__file__).parent / "static"

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        _ = app
        if settings.database_url.startswith("sqlite+"):
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        get_logger("app").info("app.startup", app_env=settings.app_env)
        try:
            yield
        finally:
            await engine.dispose()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.state.services = AppServices(settings, sessionmaker)
    app.add_middleware(RequestIdMiddleware)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def frontend() -> str:
        return (static_dir / "index.html").read_text(encoding="utf-8")

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(assessment.router)
    app.include_router(profile.router)
    app.include_router(report.router)

    return app


app = create_app()
