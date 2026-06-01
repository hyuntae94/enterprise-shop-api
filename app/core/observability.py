"""Observability: Prometheus metrics + optional OpenTelemetry tracing.

Exposes a ``/metrics`` endpoint and instruments the ASGI app with OTel when an
OTLP exporter is configured. Designed to be a no-op-safe import: if optional
packages are missing the app still boots.
"""

from __future__ import annotations

from fastapi import FastAPI, Response
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    generate_latest,
)
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["method", "path"],
)


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):  # type: ignore[no-untyped-def]
        # Use the route template (not the raw path) to keep label cardinality low.
        route = request.scope.get("route")
        path = getattr(route, "path", request.url.path)
        with REQUEST_LATENCY.labels(request.method, path).time():
            response = await call_next(request)
        REQUEST_COUNT.labels(request.method, path, response.status_code).inc()
        return response


def setup_observability(app: FastAPI) -> None:
    app.add_middleware(PrometheusMiddleware)

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    # Optional distributed tracing — only if instrumentation is importable.
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)
    except Exception:
        pass
