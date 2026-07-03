from collections.abc import Awaitable, Callable
from time import perf_counter
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger

logger = get_logger("app.api")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("x-request-id", f"req_{uuid4().hex}")
        request.state.request_id = request_id
        start = perf_counter()
        logger.info(
            "api.request.started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
        )
        try:
            response = await call_next(request)
        except Exception as exc:
            logger.error(
                "api.request.failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error_type=type(exc).__name__,
            )
            raise

        response.headers["x-request-id"] = request_id
        logger.info(
            "api.request.completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            latency_ms=round((perf_counter() - start) * 1000, 2),
        )
        return response

