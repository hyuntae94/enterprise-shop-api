---
name: scaffold-resource
description: Scaffold a complete new REST resource as a vertical slice across all layers of this FastAPI app (model, schema, repository, service, router, test) plus wiring. Use when the user asks to "add a <resource>", "scaffold <resource>", or "create a new endpoint/resource". Produces consistent boilerplate matching the products reference implementation.
---

# Scaffold a new resource

Generate a full vertical slice for a new resource named `<resource>` (singular,
snake_case). The `products` resource is the canonical reference — read it first.

## Files to create / edit
1. `app/models/<resource>.py` — `class <Resource>(Base, TimestampMixin)` with `Mapped[...]` columns. Money → `Numeric(12,2)`.
2. `app/schemas/<resource>.py` — `<Resource>Create`, `<Resource>Update`, `<Resource>Read(ORMModel)`.
3. `app/repositories/<resource>.py` — `class <Resource>Repository(BaseRepository[<Resource>])` with `model = <Resource>`.
4. `app/services/<resource>.py` — `class <Resource>Service`; raise `NotFoundError`/`ConflictError`/`BusinessRuleError` from `app/core/exceptions.py`.
5. `app/api/v1/endpoints/<resource>.py` — thin `APIRouter(prefix="/<resource>s", tags=["<resource>s"])`.
6. `app/api/deps.py` — add `get_<resource>_service(db) -> <Resource>Service`.
7. `app/api/v1/router.py` — `api_router.include_router(<resource>.router)`.
8. `app/db/base.py` — add `<resource>` to the model import line.
9. `tests/test_<resource>s.py` — happy/auth/permission/validation/not-found.

## Conventions (do not deviate)
- Reads public unless told otherwise; writes guarded by `require_staff`/`require_admin`.
- Pagination via `PageParams`/`Page` (`app/schemas/common.py`).
- Services never import FastAPI; repositories never commit; SQL only in repositories.

## Finish
- Run `python3 -m compileall app tests`.
- Tell the user to create a migration: `make revision m="add <resource>s"`.
- Summarize the files created and the new routes.

## Worked example — `reviews`
A `reviews` resource (a customer review of a product) would add:
`models/review.py` (`product_id` FK, `user_id` FK, `rating` 1–5, `body` text),
matching schemas/repo/service (block duplicate review per user+product →
`ConflictError`), endpoints `POST /reviews` (auth required), `GET
/products/{id}/reviews` (public), and tests asserting the duplicate → 409 and
rating-out-of-range → 422.
