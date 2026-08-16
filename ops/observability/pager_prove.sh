#!/usr/bin/env bash
# P2-OBS-PROD: mount the pager overlay and require a human acknowledgement.
#
#   export PAGER_WEBHOOK_URL_FILE=$HOME/.secrets/fitness-os-pager-url
#   export APPLY=1 RUN_DRILL=1 PAGER_HUMAN_ACK=1
#   ./ops/observability/pager_prove.sh
#
# Exit 2 unless a human sets PAGER_HUMAN_ACK=1 after they received the page.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

not_verified() {
  echo "NOT VERIFIED — $*" >&2
  echo "P2-OBS-PROD stays UNVERIFIED." >&2
  exit 2
}

[[ -n "${PAGER_WEBHOOK_URL_FILE:-}" ]] \
  || not_verified "PAGER_WEBHOOK_URL_FILE is not set"

FILE="$PAGER_WEBHOOK_URL_FILE"
[[ "$FILE" == /* ]] || not_verified "PAGER_WEBHOOK_URL_FILE must be an absolute path"
[[ -f "$FILE" ]] || not_verified "webhook file does not exist: $FILE"
[[ -s "$FILE" ]] || not_verified "webhook file is empty: $FILE"

URL="$(tr -d ' \t\r\n' < "$FILE")"
[[ "$URL" == https://* ]] || not_verified "webhook file must contain a single https:// URL"
# Refuse obviously committed-looking placeholders.
case "$URL" in
  *example.com*|*changeme*|*YOUR_*|*TODO*)
    not_verified "webhook URL looks like a placeholder"
    ;;
esac
echo "PASS  webhook-file — https URL present (value not printed)"

COMPOSE=(
  docker compose
  -f "$ROOT/docker-compose.yml"
  -f "$ROOT/docker-compose.obs.yml"
  -f "$ROOT/ops/observability/docker-compose.pager.yml"
)

if [[ "${APPLY:-}" == "1" ]]; then
  command -v docker >/dev/null 2>&1 || not_verified "docker is not on PATH"
  echo "remounting alertmanager with pager overlay"
  PAGER_WEBHOOK_URL_FILE="$FILE" "${COMPOSE[@]}" up -d alertmanager
  echo "PASS  overlay — alertmanager remounted with alertmanager.pager.yml"
else
  echo "APPLY is not 1 — not remounting. Compose line:"
  echo "  PAGER_WEBHOOK_URL_FILE=$FILE ${COMPOSE[*]} up -d alertmanager"
fi

if [[ "${RUN_DRILL:-}" == "1" ]]; then
  "$ROOT/ops/observability/alert_fire_drill.sh" \
    || not_verified "alert_fire_drill.sh failed (Alertmanager path not proven this run)"
  echo "PASS  fire-drill — BackendTargetDown reached Alertmanager"
else
  echo "RUN_DRILL is not 1 — skipping alert_fire_drill.sh"
fi

if [[ "${PAGER_HUMAN_ACK:-}" != "1" ]]; then
  not_verified "PAGER_HUMAN_ACK is not 1 — a human must confirm the page arrived"
fi

echo "PASS  human-ack — operator attests a human received the page"
echo
echo "ALL PASS — pager overlay + human acknowledgement recorded on this host"
echo "Paste destination + who got the page into docs/ops/OBSERVABILITY.md."
echo "Do not flip EXTERNAL_GATES.md from this output alone."
