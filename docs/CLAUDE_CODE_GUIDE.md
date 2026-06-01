# Claude Code Toolkit — Usage Guide

This project ships a complete [Claude Code](https://claude.com/claude-code)
configuration under `.claude/`, tuned to this FastAPI codebase. It demonstrates
the four main extension points:

| Capability | Lives in | Invoked |
|---|---|---|
| **Subagents** | `.claude/agents/*.md` | automatically by description, or `@agent-<name>` |
| **Skills** | `.claude/skills/<name>/SKILL.md` | automatically when the task matches |
| **Slash commands** | `.claude/commands/*.md` | you type `/<name>` |
| **Hooks** | `.claude/settings.json` + `.claude/hooks/*.sh` | automatically on tool events |

```
.claude/
├── settings.json              # permissions + hook wiring
├── agents/                    # 9 specialized subagents
│   ├── api-designer.md
│   ├── code-reviewer.md
│   ├── test-author.md
│   ├── db-migrator.md
│   ├── security-auditor.md
│   ├── performance-optimizer.md
│   ├── docs-writer.md
│   ├── refactor-specialist.md
│   └── devops-engineer.md
├── skills/                    # task playbooks (some with scripts)
│   ├── scaffold-resource/SKILL.md
│   ├── db-migration/SKILL.md
│   ├── api-smoke-test/{SKILL.md, smoke.sh}
│   └── release-prep/SKILL.md
├── commands/                  # slash commands
│   ├── check.md
│   └── add-resource.md
└── hooks/                     # event scripts
    ├── format-python.sh
    └── protect-secrets.sh
```

---

## Agents vs. Skills vs. Commands — when to use which

- **Skill** = a *playbook*. Knowledge + steps for a recurring task. Claude reads
  it and follows it **in the current conversation**. Best for "how do we do X
  here" (scaffold a resource, write a migration).
- **Subagent** = a *separate worker* with its own context window, tools, and
  system prompt. Best for focused, potentially long jobs you want isolated from
  the main thread (review this diff, audit security). Returns a summary.
- **Slash command** = a *shortcut* you type to kick off a prompt/skill/agent.
- **Hook** = *automation* that runs on tool events regardless of the model
  (formatting, guardrails).

---

## Subagents

Subagents trigger automatically when your request matches their `description`,
or you can call one explicitly with `@agent-<name>`. Each runs in its own context
so it won't clutter the main conversation.

### `api-designer`
Designs a new resource as a full vertical slice (model→schema→repo→service→
router→test) matching the codebase conventions.
```
> Add a "coupons" resource: a percentage discount with a code, validity window,
  and max redemptions. Admins manage them; customers apply a code at checkout.
```
```
> @agent-api-designer redesign the orders endpoint to support partial refunds
```

### `code-reviewer`
Read-only review of your working-tree diff for bugs, layer violations, async
pitfalls, and security gaps. Run it before committing.
```
> Review the changes I just made before I commit.
```
```
> @agent-code-reviewer is the order service ready to ship?
```

### `test-author`
Adds/expands pytest coverage using the project fixtures, then runs the suite.
```
> Write tests for the order cancel + restock flow, including the
  "can't cancel a fulfilled order" branch.
```

### `db-migrator`
Safe Alembic migrations (autogenerate + hand-edit + reversibility + zero-downtime
sequencing).
```
> Add a nullable "phone" column to users and backfill it from profile data.
```

### `security-auditor`
Defensive audit of auth, authz, input handling, secrets, and deps. Produces a
severity-ranked findings report (does not modify code).
```
> Audit the authentication and authorization before we launch.
```

### `performance-optimizer`
Finds and fixes N+1 queries, missing indexes, blocking async calls, and cache
gaps.
```
> The product list endpoint is slow under load — find and fix the bottleneck.
```

### `docs-writer`
Writes/updates docs verified against the actual code (README, API guides, ADRs,
docstrings).
```
> Write an ADR documenting why we chose arq over Celery for background jobs.
```

### `refactor-specialist`
Behavior-preserving refactors; keeps tests green.
```
> The product service mixes caching and business logic — extract the caching
  into a clean layer without changing behavior.
```

### `devops-engineer`
Containers, compose, CI/CD, deploy config, observability wiring.
```
> Add a GitHub Actions CI workflow that lints, type-checks, and runs the tests
  against service-container postgres and redis.
```

---

## Skills

Skills activate automatically when your request matches their description — you
don't have to name them. They steer Claude to follow the project's conventions.

### `scaffold-resource`
Generates a complete new resource slice (the playbook the `api-designer` agent
also follows).
```
> Scaffold a "wishlist" resource where a user saves products for later.
```

### `db-migration`
The migration workflow + safe-migration rules + exact `make` commands.
```
> I added a discount_pct field to Product — make the migration.
```

### `api-smoke-test`
End-to-end happy-path check against a running server. Ships a runnable script:
```bash
make up                                            # start the stack
make seed                                          # ensure a product exists
bash .claude/skills/api-smoke-test/smoke.sh        # register→login→list→order
# or against staging:
BASE_URL=https://staging.example.com bash .claude/skills/api-smoke-test/smoke.sh
```
```
> Smoke-test the API to confirm the deploy is healthy.
```

### `release-prep`
Runs the quality gate, summarizes commits since the last tag, and drafts a
changelog + semver recommendation.
```
> Prep a release — run the gate and write the release notes since the last tag.
```

---

## Slash commands

Type these in the Claude Code prompt:

### `/check`
Runs the full local quality gate (ruff + mypy + pytest) and reports pass/fail.
```
/check
```

### `/add-resource <name>`
Scaffolds a new resource via the `scaffold-resource` skill / `api-designer`.
```
/add-resource review
```

---

## Hooks

Hooks run automatically on tool events (configured in `.claude/settings.json`).
They execute deterministically — they are not the model "remembering" to do
something.

### `format-python.sh` — PostToolUse (Edit|Write)
After Claude edits any `.py` file, runs `ruff format` + `ruff check --fix` on it.
No-ops silently if ruff isn't installed or the file isn't Python, so it never
blocks an edit. Result: code Claude writes is always formatted to project style.

### `protect-secrets.sh` — PreToolUse (Edit|Write)
Blocks edits to `.env` / `.env.*` secret files (exit code 2 denies the tool
call), while allowing `.env.example`. Guardrail against leaking real secrets into
a tracked file.

### Permissions (`settings.json`)
Pre-allows safe, common commands (`make`, `ruff`, `mypy`, `pytest`, `alembic`,
read-only `git`) so Claude doesn't prompt for them, and denies reading `.env*`.

> **Customize:** edit `.claude/settings.json`. To temporarily disable a hook,
> comment out its block. Hooks use `$CLAUDE_PROJECT_DIR` so they work regardless
> of the current working directory.

---

## A typical workflow tying it together

```
1. /add-resource review            # scaffold the slice  (skill + api-designer)
2. (db-migrator)  > make a migration for the new reviews table
3. (test-author)  > add tests for the reviews endpoint
4. /check                          # lint + types + tests
5. (code-reviewer)> review my changes before commit
6. (security-auditor) > quick authz check on the new endpoint
7. /release-prep equivalent: > prep a release and draft notes
```

Each step either runs in the main thread (skills/commands) or hands off to an
isolated subagent, while the hooks keep formatting and secret-safety automatic
throughout.
