# Architecture

This document explains the *why* behind the structure. For the directory map see
the README.

## Request lifecycle

1. **Middleware** (`app/core/middleware.py`) assigns a request id, starts a
   timer, and enforces the Redis rate limit. CORS is applied for browser clients.
2. **Router** (`app/api/v1/endpoints/*`) matches the route. Endpoints are thin:
   they parse/validate input (Pydantic), resolve a **service** via a dependency
   factory, call it, and serialize the result.
3. **Dependency injection** (`app/api/deps.py`) is the composition root. It turns
   the request-scoped `AsyncSession` into repositories → services, resolves the
   current user from the JWT, and enforces role guards.
4. **Service** (`app/services/*`) runs business rules. It is transport-agnostic
   (no FastAPI imports) and raises domain exceptions.
5. **Repository** (`app/repositories/*`) performs data access only and never
   commits.
6. **Session/unit-of-work** (`app/db/session.py`): `get_db` yields a session,
   commits on success, rolls back on exception. One transaction per request.
7. **Exception handlers** (`app/core/exceptions.py`) translate domain errors into
   a consistent JSON envelope:
   ```json
   {"error": {"code": "not_found", "message": "...", "details": {}}}
   ```

## Key design decisions

### Layering with one-way dependencies
`api → service → repository → model`. Nothing points back up. This keeps business
logic free of framework details and makes each layer independently testable.

### The session is the unit of work
Services and repositories call `flush()` (to populate PKs / run defaults) but
never `commit()`. The request boundary owns the transaction, so a multi-step
operation like checkout is atomic by construction.

### Concurrency-safe inventory
`OrderService.create_order` locks product rows with `SELECT ... FOR UPDATE`
(`ProductRepository.get_for_update`) before decrementing stock, preventing
oversells under concurrent checkouts. Prices are **snapshotted** onto order lines
so later catalog edits don't rewrite history.

### Money is never a float
All monetary columns are `NUMERIC(12,2)` mapped to Python `Decimal`. Schemas
validate `max_digits`/`decimal_places`.

### Caching with explicit invalidation
`ProductService` read-through caches the hot first page of the catalog in Redis
and invalidates on writes. The cache **fails open** — a Redis outage degrades to
direct DB reads, never an error.

### Auth model
Stateless JWT access tokens (short-lived) + refresh tokens (long-lived). Token
*type* is checked so a refresh token can't be used as an access token. RBAC via
`UserRole` with `require_roles(...)` dependency guards; ownership checks live in
services (e.g. customers see only their own orders).

### Observability
- **Logs**: structlog, JSON in production, every line carries the `request_id`.
- **Metrics**: Prometheus `/metrics` with low-cardinality route-template labels.
- **Traces**: OpenTelemetry FastAPI instrumentation (enabled when an exporter is
  configured).

## Scaling notes
- **Stateless app** → scale horizontally behind a load balancer; readiness probe
  gates traffic during rollout.
- **DB** → async connection pool with `pool_pre_ping`; add read replicas and route
  read-only repositories to them when needed.
- **Background work** → offload slow/async side-effects (email, indexing) to arq
  workers via Redis, keeping request latency low.
- **Migrations** → run as a pre-deploy step; follow the expand/contract pattern
  for zero-downtime schema changes (see the `db-migration` skill).
