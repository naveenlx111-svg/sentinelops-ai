#!/usr/bin/env bash
# End-to-end check of a running shop, through the gateway only.
#
#   scripts/smoke.sh [GATEWAY_URL]      default: http://localhost:8000
#
# Every check crosses at least one service boundary, so a pass means the
# services can really reach each other and the database. It places one real
# order, which takes one unit of product 2 out of stock.
#
# Requires curl and jq.
set -uo pipefail

base="${1:-http://localhost:8000}"
failures=0
body="$(mktemp)"
trap 'rm -f "$body"' EXIT

# check DESCRIPTION EXPECTED_STATUS METHOD PATH [JSON_BODY]
check() {
    local description="$1" expected="$2" method="$3" path="$4" data="${5:-}"
    local status
    if [[ -n "$data" ]]; then
        status="$(curl -s -o "$body" -w '%{http_code}' --max-time 10 -X "$method" \
            -H 'content-type: application/json' -d "$data" "$base$path")"
    else
        status="$(curl -s -o "$body" -w '%{http_code}' --max-time 10 -X "$method" "$base$path")"
    fi
    if [[ "$status" == "$expected" ]]; then
        printf 'PASS  %-46s %s\n' "$description" "$status"
    else
        printf 'FAIL  %-46s got %s, expected %s: %s\n' \
            "$description" "$status" "$expected" "$(head -c 200 "$body")"
        failures=$((failures + 1))
    fi
}

check "gateway is alive"                         200 GET  /healthz
check "gateway -> catalog -> database"           200 GET  /api/products
check "gateway -> users -> database"             200 GET  /api/users/1
check "unknown user passes through as 404"       404 GET  /api/users/999999

check "gateway -> checkout -> users, catalog"    201 POST /api/orders \
    '{"user_id": 1, "product_id": 2, "quantity": 1}'
order_id="$(jq -r '.id // empty' "$body" 2>/dev/null)"
if [[ -n "$order_id" ]]; then
    check "order $order_id can be read back"               200 GET "/api/orders/$order_id"
else
    echo "FAIL  no order id returned, cannot read the order back"
    failures=$((failures + 1))
fi

check "order for an unknown user is refused"     404 POST /api/orders \
    '{"user_id": 999999, "product_id": 2, "quantity": 1}'
check "order beyond stock is refused"            409 POST /api/orders \
    '{"user_id": 1, "product_id": 2, "quantity": 1000000}'

echo
if [[ "$failures" -eq 0 ]]; then
    echo "all checks passed against $base"
else
    echo "$failures check(s) failed against $base"
    exit 1
fi
