---
name: db-migration
description: Create, review, and apply Alembic database migrations safely in this async SQLAlchemy project. Use when the user changes a model, asks to "add a column/index/table", "make a migration", "backfill data", or "migrate the database". Covers autogenerate, hand-editing, reversibility, and zero-downtime sequencing.
---

# Database migrations (async Alembic)

## Commands
```bash
make revision m="describe the change"   # alembic revision --autogenerate
make migrate                            # alembic upgrade head
alembic downgrade -1                     # roll back one revision
alembic history                          # list revisions
```

## Procedure
1. **Edit the model first** in `app/models/*` — it is the source of truth and is
   imported via `app/db/base.py` so autogenerate sees it.
2. Generate the revision, then **open the generated file and read it**.
   Autogenerate routinely misses:
   - Enum value changes (we use string enums, `native_enum=False`).
   - `server_default` additions/removals.
   - Index/constraint renames (shows as drop+create).
   - Any data backfill (it never writes these — you must).
3. Write a correct, reversible `downgrade()`.
4. If a DB is reachable, prove reversibility:
   `make migrate && alembic downgrade -1 && make migrate`.

## Zero-downtime rules
- **New NOT NULL column on a populated table** → 3 steps: add nullable(+default)
  → backfill (batched, idempotent) → set NOT NULL.
- **Rename/drop** → expand/contract over two deploys; never drop in the same
  release that stops writing the column.
- **Index on a large table** → `op.create_index(..., postgresql_concurrently=True)`
  and set the migration non-transactional.
- Keep backfills batched (e.g. 1k rows/loop) to avoid long locks.

## Example — add `discount_pct` to products
1. Add `discount_pct: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)` to `Product`.
2. `make revision m="add discount_pct to products"`.
3. Verify the generated `op.add_column(...)` has the server default; add a
   matching `op.drop_column("products", "discount_pct")` in `downgrade()`.
4. `make migrate`.
