#!/usr/bin/env bash
# Point-In-Time Recovery (PITR) drill.
#
# dr_restore_drill.sh proves a dump/restore round-trip. That is NOT PITR: it
# cannot rewind to a moment before an operator mistake. This drill proves the
# real thing — WAL archiving plus recovery to a chosen timestamp.
#
#   ./backend/scripts/pitr_drill.sh
#
# It runs against a throwaway container (fitness-os-pitr) so the dev database is
# never touched. Scenario:
#
#   1. archive_mode=on, take a base backup
#   2. INSERT "keep" row            -> before the recovery target
#   3. record recovery target time
#   4. INSERT "disaster" row        -> after the recovery target
#   5. restore base backup, replay WAL to the target time
#   6. assert "keep" survived and "disaster" is gone
#
# Exits non-zero unless step 6 holds exactly.

set -uo pipefail

CONTAINER=${CONTAINER:-fitness-os-pitr}
IMAGE=${IMAGE:-postgres:16}
PGPASSWORD_VALUE=${PGPASSWORD_VALUE:-postgres}
DB=${DB:-pitr_drill}

log() { printf '[%s] %s\n' "$(date -u +%H:%M:%S)" "$*"; }
fail() { printf 'FAIL: %s\n' "$*"; cleanup; exit 1; }

cleanup() {
  docker rm -f "$CONTAINER" >/dev/null 2>&1 || true
}
trap cleanup EXIT

psql_main() {
  docker exec -e PGPASSWORD="$PGPASSWORD_VALUE" "$CONTAINER" \
    psql -U postgres -d "$1" -tAc "$2" 2>&1
}

log "removing any previous drill container"
cleanup

log "starting $IMAGE with WAL archiving enabled"
docker run -d --name "$CONTAINER" \
  -e POSTGRES_PASSWORD="$PGPASSWORD_VALUE" \
  -e POSTGRES_INITDB_ARGS="--data-checksums" \
  "$IMAGE" \
  -c wal_level=replica \
  -c archive_mode=on \
  -c "archive_command=test ! -f /wal_archive/%f && cp %p /wal_archive/%f" \
  -c max_wal_senders=3 \
  -c archive_timeout=10s >/dev/null || fail "could not start $CONTAINER"

# The archive dir must exist and be writable before the first archive attempt.
docker exec -u root "$CONTAINER" mkdir -p /wal_archive /basebackup /restore_data
docker exec -u root "$CONTAINER" chown -R postgres:postgres /wal_archive /basebackup /restore_data
docker exec -u root "$CONTAINER" chmod 700 /restore_data

log "waiting for postgres to accept connections"
deadline=$((SECONDS + 90))
until docker exec "$CONTAINER" pg_isready -U postgres >/dev/null 2>&1; do
  (( SECONDS < deadline )) || fail "postgres never became ready"
  sleep 2
done

# Restart so archive_mode takes effect with the archive dir present.
docker restart "$CONTAINER" >/dev/null
deadline=$((SECONDS + 90))
until docker exec "$CONTAINER" pg_isready -U postgres >/dev/null 2>&1; do
  (( SECONDS < deadline )) || fail "postgres never came back after restart"
  sleep 2
done

archiving=$(psql_main postgres "SHOW archive_mode;")
[[ "$archiving" == "on" ]] || fail "archive_mode is '$archiving', expected 'on'"
log "archive_mode=on confirmed"

psql_main postgres "CREATE DATABASE $DB;" >/dev/null
psql_main "$DB" "CREATE TABLE ledger (id serial primary key, note text, at timestamptz default now());" >/dev/null

log "taking base backup"
# Must run as postgres: the official image's docker exec default is root, and a
# root-owned 0700 backup dir is unreadable by the postgres-owned recovery instance.
docker exec -u postgres -e PGPASSWORD="$PGPASSWORD_VALUE" "$CONTAINER" \
  pg_basebackup -U postgres -D /basebackup -Fp -Xs -c fast >/dev/null 2>&1 \
  || fail "pg_basebackup failed"
docker exec -u root "$CONTAINER" chown -R postgres:postgres /basebackup
log "base backup complete"

log "writing the row that must SURVIVE recovery"
psql_main "$DB" "INSERT INTO ledger (note) VALUES ('keep-me');" >/dev/null

# Let the clock advance so the recovery target is unambiguously between the
# two writes.
sleep 2
TARGET_TIME=$(psql_main postgres "SELECT now();")
[[ -n "$TARGET_TIME" ]] || fail "could not read recovery target time"
log "recovery target time: $TARGET_TIME"
sleep 2

log "writing the row that must DISAPPEAR (simulated operator mistake)"
psql_main "$DB" "INSERT INTO ledger (note) VALUES ('disaster-drop-table');" >/dev/null

before=$(psql_main "$DB" "SELECT count(*) FROM ledger;")
[[ "$before" == "2" ]] || fail "expected 2 rows before recovery, got '$before'"
log "pre-recovery row count: $before (keep-me + disaster)"

# Force a WAL segment switch so everything needed is archived.
psql_main postgres "SELECT pg_switch_wal();" >/dev/null
sleep 6

log "preparing restore from base backup"
docker exec -u postgres "$CONTAINER" bash -c "rm -rf /restore_data/* /restore_data/.[!.]* 2>/dev/null; cp -a /basebackup/. /restore_data/"
# `cp -a` stamps the source directory's mode onto the destination, so restore
# the 0700 that postgres demands of a data directory.
docker exec -u root "$CONTAINER" chmod 700 /restore_data
docker exec -u postgres "$CONTAINER" bash -c "cat >> /restore_data/postgresql.conf <<EOF
port = 5433
restore_command = 'cp /wal_archive/%f %p'
recovery_target_time = '$TARGET_TIME'
recovery_target_action = 'promote'
archive_mode = off
EOF"
docker exec -u postgres "$CONTAINER" touch /restore_data/recovery.signal

log "starting recovery instance on port 5433"
docker exec -u postgres "$CONTAINER" \
  pg_ctl -D /restore_data -l /tmp/restore.log -w -t 120 start >/dev/null 2>&1

deadline=$((SECONDS + 120))
until docker exec "$CONTAINER" pg_isready -U postgres -p 5433 >/dev/null 2>&1; do
  if (( SECONDS >= deadline )); then
    docker exec "$CONTAINER" tail -30 /tmp/restore.log
    fail "recovery instance never became ready"
  fi
  sleep 2
done
log "recovery instance is up"

in_recovery=$(docker exec -e PGPASSWORD="$PGPASSWORD_VALUE" "$CONTAINER" \
  psql -U postgres -p 5433 -d postgres -tAc "SELECT pg_is_in_recovery();" 2>&1)
log "pg_is_in_recovery() = $in_recovery"

rows=$(docker exec -e PGPASSWORD="$PGPASSWORD_VALUE" "$CONTAINER" \
  psql -U postgres -p 5433 -d "$DB" -tAc "SELECT note FROM ledger ORDER BY id;" 2>&1)
log "rows after recovery: $(echo "$rows" | tr '\n' ' ')"

echo "$rows" | grep -q "keep-me" \
  || fail "'keep-me' is missing — recovery lost committed data before the target"
if echo "$rows" | grep -q "disaster-drop-table"; then
  fail "'disaster-drop-table' survived — recovery did NOT stop at the target time"
fi

count=$(docker exec -e PGPASSWORD="$PGPASSWORD_VALUE" "$CONTAINER" \
  psql -U postgres -p 5433 -d "$DB" -tAc "SELECT count(*) FROM ledger;" 2>&1)
[[ "$count" == "1" ]] || fail "expected exactly 1 row after recovery, got '$count'"

archived=$(psql_main postgres "SELECT archived_count, failed_count FROM pg_stat_archiver;")
log "pg_stat_archiver (archived, failed): $archived"

cat <<EOF

=== PITR DRILL PASSED ===
  base backup      : pg_basebackup -Fp -Xs
  recovery target  : $TARGET_TIME
  rows before      : 2 (keep-me, disaster-drop-table)
  rows after       : 1 (keep-me)
  disaster row     : correctly absent
  archiver         : $archived
EOF
