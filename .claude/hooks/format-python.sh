#!/usr/bin/env bash
# PostToolUse hook: auto-format edited Python files with ruff.
# Receives the tool-call JSON on stdin. No-ops gracefully if ruff is missing
# or the edited file isn't Python, so it never blocks an edit.
set -euo pipefail

input="$(cat)"

# Extract the edited file path from the hook payload (python is always present
# in this repo's toolchain; falls back silently if not).
file="$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    data = json.load(sys.stdin)
    print(data.get("tool_input", {}).get("file_path", ""))
except Exception:
    print("")
' 2>/dev/null || true)"

case "$file" in
  *.py) ;;            # proceed
  *) exit 0 ;;        # not python -> nothing to do
esac

[ -f "$file" ] || exit 0
command -v ruff >/dev/null 2>&1 || exit 0   # ruff not installed -> skip

ruff format "$file" >/dev/null 2>&1 || true
ruff check --fix "$file" >/dev/null 2>&1 || true
exit 0
