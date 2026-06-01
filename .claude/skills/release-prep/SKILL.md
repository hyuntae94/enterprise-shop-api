---
name: release-prep
description: Prepare a release — run the full quality gate (lint, types, tests), summarize the changes since the last tag into release notes, and produce a conventional-commit-style changelog. Use when the user asks to "prep a release", "cut a version", "write release notes", or "what changed since last release".
---

# Release preparation

## 1. Quality gate (must all pass)
```bash
make lint      # ruff
make type      # mypy
make test      # pytest with coverage
```
If any fail, stop and report — do not draft notes for a red build.

## 2. Collect changes
```bash
git describe --tags --abbrev=0 2>/dev/null   # last tag (may be empty)
git log <last-tag>..HEAD --pretty=format:'%s (%h)'
```
If there is no prior tag, summarize all of `git log`.

## 3. Group into changelog sections
Bucket commits by Conventional Commit prefix:
- **Features** ← `feat:`
- **Fixes** ← `fix:`
- **Performance** ← `perf:`
- **Refactors / Internal** ← `refactor:`, `chore:`, `test:`, `ci:`
- **Breaking changes** ← any `!` or `BREAKING CHANGE:` footer (call out loudly)

## 4. Output
Write `CHANGELOG.md` (prepend a new version section, dated) and a short
GitHub-release-ready summary. Suggest the next semver bump based on the
contents (breaking → major, feat → minor, else patch). Do NOT create the tag
or push unless the user explicitly asks.
