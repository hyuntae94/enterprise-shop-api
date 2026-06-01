"""Application factory and ASGI entrypoint.

Run locally:    uvicorn app.main:app --reload
Run in prod:    gunicorn app.main:app -k uvicorn.workers.UvicornWorker
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.middleware import RateLimitMiddleware, RequestContextMiddleware
from app.core.observability import setup_observability
from app.db.redis import close_redis
from app.db.session import dispose_engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):  # type: ignore[no-untyped-def]
    """Startup/shutdown hooks — own resources here, not at import time."""
    configure_logging(level=settings.LOG_LEVEL, json_logs=settings.LOG_JSON)
    logger.info("startup", environment=settings.ENVIRONMENT, app=settings.APP_NAME)
    yield
    logger.info("shutdown")
    await dispose_engine()
    await close_redis()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        debug=settings.DEBUG,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Middleware is applied bottom-up: context (outermost) → rate limit → CORS.
    if settings.BACKEND_CORS_ORIGINS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.BACKEND_CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)
    setup_observability(app)

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    @app.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {"service": settings.APP_NAME, "docs": "/docs"}

    return app


app = create_app()
