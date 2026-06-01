#!/usr/bin/env bash
# PreToolUse hook: block edits to real secret files (.env) while allowing
# .env.example. Exit code 2 tells Claude Code to deny the tool call.
set -euo pipefail

input="$(cat)"
file="$(printf '%s' "$input" | python3 -c '
import json, sys
try:
    print(json.load(sys.stdin).get("tool_input", {}).get("file_path", ""))
except Exception:
    print("")
' 2>/dev/null || true)"

base="$(basename "$file")"
if [ "$base" = ".env" ] || { case "$base" in .env.*) [ "$base" != ".env.example" ];; *) false;; esac; }; then
  echo "Refusing to edit secret file '$base'. Edit .env.example instead and set real values manually." >&2
  exit 2
fi
exit 0
