# Production WAL / RPO contract

**Status:** **UNVERIFIED** · P1-10-PROD

Index: `docs/ops/EXTERNAL_GATES.md`. Local PITR mechanics already passed
(`docs/ops/DR_RESTORE_STATUS.md`) against a disposable container. That
drill is **not** production RPO. Target (ADR-042): RPO ≤ 5 minutes.

## Close this gate (one command)

Owner: **A-OPS**. Pick **one** of the two environment shapes.

Managed RDS / Aurora:

```bash
export AWS_REGION=eu-central-1
export RDS_INSTANCE_ID=fitness-os-prod
export RESTORE_DRILL_DATE=2026-mm-dd          # last successful restore
./ops/wal/prod_rpo.sh
```

Self-hosted Postgres with off-host `archive_command`:

```bash
export PGHOST=... PGUSER=... PGDATABASE=postgres
export RESTORE_DRILL_DATE=2026-mm-dd
./ops/wal/prod_rpo.sh
```

The script asserts continuous off-host archive (or a provider PITR
window) and that `LatestRestorableTime` / `last_archived_wal` is within
300 seconds. It will **not** write canary rows on the production
primary. A restore drill date is mandatory — configuration without a
recorded restore is still UNVERIFIED.

Exit 2 = `NOT VERIFIED`.

## Required on the production host

1. Continuous **off-host** WAL archive (object storage or the managed
   provider's PITR). WAL that lives only on the database volume is not
   an archive.
2. Measured RPO: `LatestRestorableTime` (RDS) or `pg_stat_archiver`
   last success within 5 minutes, **plus** a restore drill that proved
   a canary survived and a later disaster write did not.
3. Scheduled restore drill (quarterly at minimum). Record the date in
   `RESTORE_DRILL_DATE` and in the log below.

## Managed Postgres

If the platform is RDS / Cloud SQL / Crunchy / similar, enable the
provider PITR window and record:

- retention (hours/days)
- last successful restore drill date
- measured RPO from that drill

Do not mark P1-10-PROD closed until those three exist.

## Self-hosted archive_command shape

Acceptable destinations are object storage or a remote WAL service
(wal-g, pgBackRest, Barman, `aws s3 cp`, vendor archive). A local
`cp %p /var/lib/postgresql/wal_archive/%f` on the same volume is
**not** off-host. `archive_timeout` must be ≤ 300s to meet RPO.

The local container drill (`backend/scripts/pitr_drill.sh`) remains
the mechanics proof. Re-run it against a clone of production, not
against the live primary, after off-host archive is on.

## Evidence log

| Date | Host / instance | Retention | Measured RPO | Restore drill | Result |
|---|---|---|---|---|---|
| — | — | — | — | — | **Never measured on a production host.** |

## What not to do

Do not treat `pg_dump` alone as PITR. Do not commit WAL files. Do not
write the local container drill into the table above.
