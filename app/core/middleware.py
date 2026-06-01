"""Cross-cutting HTTP middleware.

* RequestContextMiddleware  — assigns a request id, times the request, logs it.
* RateLimitMiddleware       — simple fixed-window limiter backed by Redis.
"""

from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.core.logging import get_logger, request_id_ctx

logger = get_logger("http")


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Bind a request id, measure latency, and emit one structured access log."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        rid = request.headers.get("X-Request-ID", uuid.uuid4().hex)
        token = request_id_ctx.set(rid)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        response.headers["X-Request-ID"] = rid
        response.headers["X-Process-Time-ms"] = str(elapsed_ms)
        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=elapsed_ms,
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window per-client rate limit using Redis INCR + EXPIRE.

    Keyed by authenticated subject when available, else client IP. Fails open
    if Redis is unavailable so a cache outage never takes down the API.
    """

    def __init__(self, app, limit_per_minute: int | None = None) -> None:
        super().__init__(app)
        self.limit = limit_per_minute or settings.RATE_LIMIT_PER_MINUTE

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        from app.db.redis import get_redis  # local import avoids import cycle

        client = request.client.host if request.client else "anonymous"
        window = int(time.time() // 60)
        key = f"ratelimit:{client}:{window}"

        try:
            redis = get_redis()
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, 60)
        except Exception:  # noqa: BLE001 — fail open on cache problems
            logger.warning("rate_limit_redis_unavailable")
            return await call_next(request)

        if current > self.limit:
            return JSONResponse(
                status_code=429,
                content={
                    "error": {
                        "code": "rate_limited",
                        "message": "Too many requests",
                        "details": {"limit_per_minute": self.limit},
                    }
                },
                headers={"Retry-After": "60"},
            )
        return await call_next(request)
