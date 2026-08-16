#!/usr/bin/env bash
# Alert-path drill: prove BackendTargetDown actually fires and reaches
# Alertmanager, then restore the backend. Run against the dev observability
# overlay (docker-compose.obs.yml).
#
#   ./ops/observability/alert_fire_drill.sh
#
# Exits non-zero if the alert never fires or never reaches Alertmanager.

set -uo pipefail

PROM=${PROM:-http://localhost:9090}
ALERTMANAGER=${ALERTMANAGER:-http://localhost:9093}
TARGET=${TARGET:-fitness-os-backend}
ALERT=${ALERT:-BackendTargetDown}
DEADLINE=${DEADLINE:-300}

log() { printf '[%s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }

rule_state() {
  curl -s "$PROM/api/v1/rules" \
    | python3 -c "
import json,sys
d=json.load(sys.stdin)
for g in d['data']['groups']:
    for r in g['rules']:
        if r.get('name')=='$ALERT':
            print(r.get('state','unknown')); sys.exit(0)
print('missing')
"
}

am_has_alert() {
  curl -s "$ALERTMANAGER/api/v2/alerts" \
    | python3 -c "
import json,sys
try: d=json.load(sys.stdin)
except Exception: print('no'); sys.exit(0)
print('yes' if any(a.get('labels',{}).get('alertname')=='$ALERT' for a in d) else 'no')
"
}

restore() {
  log "restoring $TARGET"
  docker start "$TARGET" >/dev/null 2>&1
}
trap restore EXIT

log "baseline rule state: $(rule_state)"
log "stopping $TARGET to induce a scrape failure"
docker stop "$TARGET" >/dev/null || { log "FAIL: could not stop $TARGET"; exit 1; }

fired=0
start=$SECONDS
while (( SECONDS - start < DEADLINE )); do
  state=$(rule_state)
  log "rule state: $state"
  if [[ "$state" == "firing" ]]; then fired=1; break; fi
  sleep 10
done

if (( fired == 0 )); then
  log "FAIL: $ALERT never reached 'firing' within ${DEADLINE}s"
  exit 1
fi
log "PASS: $ALERT is firing"

delivered=0
start=$SECONDS
while (( SECONDS - start < 90 )); do
  if [[ "$(am_has_alert)" == "yes" ]]; then delivered=1; break; fi
  sleep 5
done

if (( delivered == 0 )); then
  log "FAIL: $ALERT never reached Alertmanager"
  exit 1
fi
log "PASS: $ALERT present in Alertmanager"

restore
trap - EXIT

start=$SECONDS
while (( SECONDS - start < 120 )); do
  if [[ "$(rule_state)" == "inactive" ]]; then
    log "PASS: $ALERT resolved after restore"
    exit 0
  fi
  sleep 10
done

log "WARN: alert still not resolved 120s after restore (check the target)"
exit 1
