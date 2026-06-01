---
description: Run the full local quality gate (ruff lint + mypy + pytest) and summarize results
allowed-tools: Bash(make:*), Bash(ruff:*), Bash(mypy:*), Bash(pytest:*), Bash(python3:*)
---

Run the project's quality gate and report a concise pass/fail summary.

1. `make lint` (ruff). If ruff isn't installed, fall back to `python3 -m compileall app tests`.
2. `make type` (mypy) — report errors grouped by file.
3. `make test` (pytest) — report failures with the assertion and `file:line`.

For each step say ✅/❌ and the key output. End with an overall verdict and, if
anything failed, the single most important thing to fix first. Do not fix
anything unless I ask — this command only reports.
