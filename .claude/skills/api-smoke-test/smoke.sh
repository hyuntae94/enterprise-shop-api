#!/usr/bin/env bash
# End-to-end smoke test for the Enterprise Shop API.
# Usage: [BASE_URL=http://host:port] bash smoke.sh
set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
API="$BASE_URL/api/v1"
EMAIL="smoke+$(date +%s)@example.com"
PASS="smoketest123"

pass() { printf '  \033[32m✓\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m✗ %s\033[0m\n' "$1"; exit 1; }

# Assert HTTP status. $1=expected $2=actual $3=label $4=body
check() { [ "$2" = "$1" ] && pass "$3 ($2)" || fail "$3: expected $1, got $2 — $4"; }

req() { # method path [json] [auth] -> sets $BODY, $CODE
  local method=$1 path=$2 data=${3:-} auth=${4:-}
  local args=(-sS -w '\n%{http_code}' -X "$method" "$API$path" -H 'Content-Type: application/json')
  [ -n "$data" ] && args+=(-d "$data")
  [ -n "$auth" ] && args+=(-H "Authorization: Bearer $auth")
  local out; out=$(curl "${args[@]}")
  CODE="${out##*$'\n'}"; BODY="${out%$'\n'*}"
}

echo "Smoke testing $BASE_URL"

req GET /health/ready
check 200 "$CODE" "health ready" "$BODY"

req POST /auth/register "{\"email\":\"$EMAIL\",\"password\":\"$PASS\",\"full_name\":\"Smoke\"}"
check 201 "$CODE" "register" "$BODY"

req POST /auth/login "{\"email\":\"$EMAIL\",\"password\":\"$PASS\"}"
check 200 "$CODE" "login" "$BODY"
TOKEN=$(printf '%s' "$BODY" | sed -n 's/.*"access_token":"\([^"]*\)".*/\1/p')
[ -n "$TOKEN" ] && pass "got access token" || fail "no access token in $BODY"

req GET "/products?size=1"
check 200 "$CODE" "list products" "$BODY"
PID=$(printf '%s' "$BODY" | sed -n 's/.*"items":\[{"[^}]*"id":\([0-9]*\).*/\1/p')

if [ -n "$PID" ]; then
  req POST /orders "{\"items\":[{\"product_id\":$PID,\"quantity\":1}]}" "$TOKEN"
  check 201 "$CODE" "create order" "$BODY"
else
  printf '  \033[33m! skipping order step (no products — run `make seed`)\033[0m\n'
fi

printf '\n\033[32mSmoke test passed.\033[0m\n'
