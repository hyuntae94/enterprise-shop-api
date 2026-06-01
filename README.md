# Enterprise Shop API

An enterprise-grade e-commerce backend built with **FastAPI**, **async
SQLAlchemy 2.0**, **PostgreSQL**, and **Redis** — structured as a clean,
layered architecture and shipped with a full **Claude Code** agent/skill toolkit
for day-to-day development.

> Sample domain: Users/Auth · Products · Orders · Payments.
> The architecture is production-shaped and domain-agnostic.

---

## Quick start

```bash
cp .env.example .env                 # then edit SECRET_KEY etc.
make up                              # build & run api + worker + postgres + redis
# API:     http://localhost:8000
# Docs:    http://localhost:8000/docs
# Metrics: http://localhost:8000/metrics
make seed                            # demo admin + products (in another shell)
```

Local (without Docker — needs Postgres & Redis running):

```bash
make install                         # venv + deps
make migrate                         # alembic upgrade head
make dev                             # uvicorn with reload
```

Common tasks: `make help`.

---

## Architecture

A strict **layered architecture** with one-directional dependencies:

```
            HTTP request
                 │
   ┌─────────────▼──────────────┐
   │  API layer  (app/api)      │  routers · deps (DI) · auth guards
   │  - thin endpoints          │
   └─────────────┬──────────────┘
                 │ calls
   ┌─────────────▼──────────────┐
   │  Service layer (services)  │  business rules · transactions · raises
   │  - transport-agnostic      │  domain exceptions · no FastAPI imports
   └─────────────┬──────────────┘
                 │ uses
   ┌─────────────▼──────────────┐
   │  Repository layer (repos)  │  data access only · never commits
   └─────────────┬──────────────┘
                 │ maps
   ┌─────────────▼──────────────┐
   │  Models (SQLAlchemy 2.0)   │  ← Pydantic schemas validate the edges
   └─────────────┬──────────────┘
                 │
         PostgreSQL · Redis
```

**Why this shape**
- *Testable*: services hold logic and don't touch HTTP → unit-testable; the API
  layer is thin → integration-testable with overridden deps.
- *Swappable*: repositories isolate SQL; the transport could change without
  touching business rules.
- *Safe transactions*: the request-scoped session is the unit of work — it
  commits on success / rolls back on error, so services never call `commit`.

### Cross-cutting concerns
| Concern | Where |
|---|---|
| Config (12-factor) | `app/core/config.py` (pydantic-settings, cached) |
| Structured logging | `app/core/logging.py` (structlog, per-request id) |
| Error envelope | `app/core/exceptions.py` (domain errors → HTTP) |
| AuthN/AuthZ | `app/core/security.py` (JWT/bcrypt) + `app/api/deps.py` (guards) |
| Rate limiting | `app/core/middleware.py` (Redis fixed-window, fail-open) |
| Observability | `app/core/observability.py` (Prometheus `/metrics`, OTel) |
| Caching | `app/services/product.py` (read-through + invalidation) |
| Background jobs | `app/workers/tasks.py` (arq) |
| Migrations | `alembic/` (async, autogenerate) |

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full tour.

---

## Project layout

```
app/
  api/          # routers, dependency injection, auth guards
  core/         # config, security, logging, exceptions, middleware, observability
  db/           # async engine/session, redis client, declarative base
  models/       # SQLAlchemy 2.0 ORM models
  schemas/      # Pydantic v2 request/response models
  repositories/ # data-access layer (no business logic)
  services/     # business logic (no transport)
  workers/      # arq background tasks
  scripts/      # seed and ops scripts
alembic/        # migrations (async env)
tests/          # pytest suite (in-memory SQLite, async client)
.claude/        # Claude Code agents, skills, commands, hooks, settings
docs/           # architecture + Claude Code usage guide
```

---

## Testing & quality

```bash
make test     # pytest + coverage
make lint     # ruff
make type     # mypy (strict)
```

Tests run against an in-memory SQLite DB with the `get_db` dependency overridden,
so they need no external services.

---

## Claude Code toolkit

This repo ships a complete **Claude Code** setup under `.claude/` — subagents,
skills, slash commands, and safety hooks tuned to this codebase. See
**[`docs/CLAUDE_CODE_GUIDE.md`](docs/CLAUDE_CODE_GUIDE.md)** for what each one
does and copy-paste examples of how to drive them.
