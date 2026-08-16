#!/usr/bin/env bash
# Live HA check. Smoke the HTTPS API and require operator evidence that
# the platform is not the single-replica compose reference.
#
#   SMOKE_BASE_URL=https://api.example.com \
#   BACKEND_REPLICA_EVIDENCE=/path/replicas.txt \
#   MULTI_AZ_EVIDENCE=/path/multiaz.txt \
#     ./ops/ha/live_check.sh
#
# Exit 2 = NOT VERIFIED.
set -euo pipefail

not_verified() {
  echo "NOT VERIFIED — $*" >&2
  echo "Live HA stays UNVERIFIED." >&2
  exit 2
}

[[ -n "${SMOKE_BASE_URL:-}" ]] || not_verified "SMOKE_BASE_URL is not set"
[[ "$SMOKE_BASE_URL" == https://* ]] \
  || not_verified "SMOKE_BASE_URL must be https:// (got $SMOKE_BASE_URL)"

case "$SMOKE_BASE_URL" in
  *localhost*|*127.0.0.1*|*0.0.0.0*|*\[::1\]*)
    not_verified "SMOKE_BASE_URL points at loopback — not a live host"
    ;;
esac

command -v curl >/dev/null 2>&1 || not_verified "curl is not on PATH"

CURL_OPTS=( -sS --max-time 15 )
# Fail closed if the cert is bad; SMOKE_INSECURE=1 is staging-only and
# does not close this gate.
if [[ "${SMOKE_INSECURE:-}" == "1" ]]; then
  echo "WARN  SMOKE_INSECURE=1 — TLS is not being verified; HA stays unproven"
  CURL_OPTS+=( -k )
fi

BODY="$(mktemp)"
trap 'rm -f "$BODY"' EXIT
for path in /live /ready; do
  code="$(curl "${CURL_OPTS[@]}" -o "$BODY" -w '%{http_code}' \
    "${SMOKE_BASE_URL}${path}" || true)"
  if [[ "$code" != "200" ]]; then
    cat "$BODY" >&2 || true
    not_verified "${path} -> HTTP ${code:-none}"
  fi
  echo "PASS  smoke ${path} -> 200"
done

need_file() {
  local var="$1"
  local path="${!var:-}"
  [[ -n "$path" ]] || not_verified "$var is not set"
  [[ -f "$path" && -s "$path" ]] || not_verified "$var file missing or empty: $path"
  # Reject files that are clearly a placeholder comment.
  if grep -Eiq 'todo|placeholder|not yet|laptop|compose.prod|single-replica' "$path"; then
    not_verified "$var looks like a placeholder, not captured platform output"
  fi
  echo "PASS  $var — $(wc -l < "$path" | tr -d ' ') lines of operator evidence"
}

need_file BACKEND_REPLICA_EVIDENCE
need_file MULTI_AZ_EVIDENCE

echo
echo "ALL PASS — HTTPS smoke + operator evidence files present"
echo "Record replica/Multi-AZ facts in docs/ops/HA_TOPOLOGY.md."
echo "Do not flip EXTERNAL_GATES.md from a laptop or from smoke.sh alone."
