---
name: api-smoke-test
description: Run an end-to-end smoke test against a running instance of this API — register, log in, browse products, place an order — to confirm the happy path works after a change or deploy. Use when the user asks to "smoke test", "verify the API works", "hit the endpoints", or "check the deploy". Includes a ready-to-run script.
---

# API smoke test

Exercises the core e-commerce flow against a live server (default
`http://localhost:8000`). Use after `make up`/deploy to confirm the path works.

## Run it
```bash
# Start the stack first (in another shell): make up
bash .claude/skills/api-smoke-test/smoke.sh                 # localhost:8000
BASE_URL=https://staging.example.com bash .claude/skills/api-smoke-test/smoke.sh
```

## What it checks
1. `GET /api/v1/health/ready` → dependencies healthy.
2. `POST /api/v1/auth/register` then `/auth/login` → token pair.
3. `GET /api/v1/products` → catalog lists.
4. `POST /api/v1/orders` → order created, stock reserved.
5. Asserts each step's HTTP status; exits non-zero on first failure.

## How to use the result
- Green: the deployed build serves the full happy path.
- Red: report which step failed with its status/body. For auth failures check
  `SECRET_KEY`; for 5xx check `make logs`; for readiness check Postgres/Redis.

Requires the catalog to have at least one in-stock product — run
`make seed` first if the order step 404s.
