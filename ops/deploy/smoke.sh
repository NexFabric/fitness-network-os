#!/usr/bin/env bash
# Post-rollout smoke: liveness and readiness must both be 200.
set -euo pipefail

BASE_URL="${SMOKE_BASE_URL:-http://127.0.0.1:8000}"

check() {
  local path="$1"
  local code
  code="$(curl -sS -o /tmp/fitness-os-smoke.body -w '%{http_code}' "${BASE_URL}${path}")"
  if [[ "$code" != "200" ]]; then
    echo "SMOKE FAIL ${path} -> HTTP ${code}" >&2
    cat /tmp/fitness-os-smoke.body >&2 || true
    exit 1
  fi
  echo "SMOKE PASS ${path} -> 200"
}

check /live
check /ready
echo "smoke ok"
