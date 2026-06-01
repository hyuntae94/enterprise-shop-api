"""Background tasks via arq (async Redis-backed task queue).

Run a worker:   arq app.workers.tasks.WorkerSettings

Enqueue from request handlers:
    from arq import create_pool
    from arq.connections import RedisSettings
    pool = await create_pool(RedisSettings(host=...))
    await pool.enqueue_job("send_order_confirmation", order_id)
"""

from __future__ import annotations

from typing import Any

from arq.connections import RedisSettings

from app.core.config import settings
from app.core.logging import configure_logging, get_logger

logger = get_logger("worker")


async def send_order_confirmation(ctx: dict[str, Any], order_id: int) -> None:
    """Example task: email an order confirmation (stubbed)."""
    logger.info("send_order_confirmation", order_id=order_id)
    # Integrate a real provider (SES, SendGrid, ...) here.


async def reindex_product(ctx: dict[str, Any], product_id: int) -> None:
    """Example task: push a product to a search index (stubbed)."""
    logger.info("reindex_product", product_id=product_id)


async def _startup(ctx: dict[str, Any]) -> None:
    configure_logging(level=settings.LOG_LEVEL, json_logs=settings.LOG_JSON)
    logger.info("worker_startup")


async def _shutdown(ctx: dict[str, Any]) -> None:
    logger.info("worker_shutdown")


class WorkerSettings:
    """arq entrypoint configuration."""

    functions = [send_order_confirmation, reindex_product]
    on_startup = _startup
    on_shutdown = _shutdown
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        database=settings.REDIS_DB,
    )
    max_jobs = 20
    job_timeout = 60
