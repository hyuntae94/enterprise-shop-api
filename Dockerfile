# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------
# Multi-stage build for a small, production-ready image.
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Build dependencies needed for asyncpg / bcrypt wheels
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the metadata and source needed to build the wheel. The hatchling backend
# reads README.md (project.readme) and packages the app/ tree, so both must be
# present before install — copying just these keeps the dependency layer cached
# across changes to tests/, docs/, etc.
COPY pyproject.toml README.md ./
COPY app ./app
# Install into an isolated prefix that we copy into the runtime stage.
RUN pip install --prefix=/install ".[dev]"

# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/install/lib/python3.11/site-packages"

# Run as a non-root user.
RUN groupadd -r app && useradd -r -g app app
WORKDIR /app

COPY --from=builder /install /install
COPY . .

USER app

EXPOSE 8000

# Healthcheck hits the liveness probe.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/api/v1/health/live').status==200 else 1)"

# Production entrypoint: gunicorn managing uvicorn workers.
CMD ["gunicorn", "app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
