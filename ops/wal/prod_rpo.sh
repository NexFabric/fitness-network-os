#!/usr/bin/env bash
# P1-10-PROD: prove continuous off-host WAL / provider PITR and RPO ≤ 5 min.
#
# Managed:
#   AWS_REGION=... RDS_INSTANCE_ID=... RESTORE_DRILL_DATE=YYYY-MM-DD \
#     ./ops/wal/prod_rpo.sh
#
# Self-hosted:
#   PGHOST=... PGUSER=... PGDATABASE=postgres RESTORE_DRILL_DATE=YYYY-MM-DD \
#     ./ops/wal/prod_rpo.sh
#
# Does not write rows on the production primary. Exit 2 = NOT VERIFIED.
set -euo pipefail

not_verified() {
  echo "NOT VERIFIED — $*" >&2
  echo "P1-10-PROD stays UNVERIFIED." >&2
  exit 2
}

RPO_SECONDS="${RPO_SECONDS:-300}"

[[ -n "${RESTORE_DRILL_DATE:-}" ]] \
  || not_verified "RESTORE_DRILL_DATE is not set (last successful restore drill)"

if [[ ! "$RESTORE_DRILL_DATE" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  not_verified "RESTORE_DRILL_DATE must be YYYY-MM-DD, got ${RESTORE_DRILL_DATE}"
fi

# A date in the future is not a drill.
TODAY="$(date -u +%F)"
if [[ "$RESTORE_DRILL_DATE" > "$TODAY" ]]; then
  not_verified "RESTORE_DRILL_DATE $RESTORE_DRILL_DATE is in the future"
fi

if [[ -n "${RDS_INSTANCE_ID:-}" ]]; then
  command -v aws >/dev/null 2>&1 || not_verified "aws CLI is not on PATH"
  [[ -n "${AWS_REGION:-}" ]] || not_verified "AWS_REGION is required with RDS_INSTANCE_ID"
  if ! aws sts get-caller-identity >/dev/null 2>&1; then
    not_verified "no usable AWS credentials"
  fi

  JSON="$(aws rds describe-db-instances \
    --db-instance-identifier "$RDS_INSTANCE_ID" \
    --query 'DBInstances[0].{MultiAZ:MultiAZ,BackupRetentionPeriod:BackupRetentionPeriod,LatestRestorableTime:LatestRestorableTime,Status:DBInstanceStatus}' \
    --output json)" || not_verified "describe-db-instances failed for $RDS_INSTANCE_ID"

  python3 - "$JSON" "$RPO_SECONDS" "$RDS_INSTANCE_ID" <<'PY'
import json, sys
from datetime import datetime, timezone

doc = json.loads(sys.argv[1])
limit = int(sys.argv[2])
ident = sys.argv[3]
retention = doc.get("BackupRetentionPeriod") or 0
latest = doc.get("LatestRestorableTime")
status = doc.get("Status")
multiaz = doc.get("MultiAZ")

if retention < 1:
    raise SystemExit(f"{ident}: BackupRetentionPeriod={retention} (need ≥ 1 day / PITR window)")
if not latest:
    raise SystemExit(f"{ident}: LatestRestorableTime is empty")

# AWS may return ISO with or without timezone.
ts = latest.replace("Z", "+00:00")
when = datetime.fromisoformat(ts)
if when.tzinfo is None:
    when = when.replace(tzinfo=timezone.utc)
age = (datetime.now(timezone.utc) - when).total_seconds()
if age > limit:
    raise SystemExit(
        f"{ident}: LatestRestorableTime is {age:.0f}s old (limit {limit}s) — {latest}"
    )
print(f"PASS  rds-pitr — instance={ident} status={status} MultiAZ={multiaz}")
print(f"PASS  rds-retention — BackupRetentionPeriod={retention}d")
print(f"PASS  rds-rpo — LatestRestorableTime={latest} age={age:.0f}s")
PY

elif [[ -n "${PGHOST:-}" || -n "${DATABASE_URL:-}" ]]; then
  command -v psql >/dev/null 2>&1 || not_verified "psql is not on PATH"
  export PGDATABASE="${PGDATABASE:-postgres}"

  archive_mode="$(psql -tAc 'SHOW archive_mode;')" || not_verified "psql SHOW archive_mode failed"
  [[ "$archive_mode" == "on" ]] || not_verified "archive_mode=$archive_mode (expected on)"

  archive_command="$(psql -tAc 'SHOW archive_command;')"
  case "$archive_command" in
    *s3*|*wal-g*|*pgbackrest*|*barman*|*walg*|*rclone*|*aws\ s3*)
      echo "PASS  archive-command — off-host shape: $archive_command"
      ;;
    *%p*|/var/*|/wal_archive*|*cp\ %p*)
      not_verified "archive_command looks on-host: $archive_command"
      ;;
    *)
      not_verified "archive_command is not a recognised off-host destination: $archive_command"
      ;;
  esac

  archive_timeout="$(psql -tAc 'SHOW archive_timeout;')"
  python3 - "$archive_timeout" "$RPO_SECONDS" <<'PY'
import sys
raw, limit = sys.argv[1], int(sys.argv[2])
# SHOW archive_timeout returns e.g. "5min" or "300s" or "0".
text = raw.strip().lower()
if text in {"0", "0s", "off"}:
    raise SystemExit(f"archive_timeout={raw} — WAL may sit unarchived longer than RPO")
mult = 1
if text.endswith("min"):
    mult, text = 60, text[:-3]
elif text.endswith("s"):
    text = text[:-1]
elif text.endswith("ms"):
    mult, text = 0.001, text[:-2]
try:
    seconds = float(text) * mult
except ValueError as exc:
    raise SystemExit(f"cannot parse archive_timeout={raw!r}") from exc
if seconds > limit:
    raise SystemExit(f"archive_timeout={raw} ({seconds}s) exceeds RPO {limit}s")
print(f"PASS  archive-timeout — {raw} ({seconds:.0f}s ≤ {limit}s)")
PY

  python3 - "$(psql -tAc "SELECT COALESCE(last_archived_time::text,''), failed_count FROM pg_stat_archiver;")" \
    "$RPO_SECONDS" <<'PY'
import sys
from datetime import datetime, timezone
row, limit = sys.argv[1], int(sys.argv[2])
parts = [p.strip() for p in row.split("|")]
last = parts[0] if parts else ""
failed = parts[1] if len(parts) > 1 else "?"
if not last:
    raise SystemExit("pg_stat_archiver.last_archived_time is empty")
when = datetime.fromisoformat(last.replace("Z", "+00:00"))
if when.tzinfo is None:
    when = when.replace(tzinfo=timezone.utc)
age = (datetime.now(timezone.utc) - when).total_seconds()
if age > limit:
    raise SystemExit(f"last_archived_time is {age:.0f}s old (limit {limit}s)")
print(f"PASS  archiver — last={last} age={age:.0f}s failed_count={failed}")
PY
else
  not_verified "set RDS_INSTANCE_ID+AWS_REGION or PGHOST/DATABASE_URL"
fi

echo "PASS  restore-drill-date — $RESTORE_DRILL_DATE (operator attestation)"
echo
echo "ALL PASS — off-host archive / provider PITR looks inside RPO ${RPO_SECONDS}s"
echo "Attach the restore-drill log to docs/ops/WAL_ARCHIVE.md."
echo "Do not flip EXTERNAL_GATES.md from this output alone."
