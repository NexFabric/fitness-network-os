# Production WAL / RPO contract

**Status:** **PROCEDURE LANDED · PRODUCTION RPO UNVERIFIED**

Local PITR mechanics already passed (`docs/ops/DR_RESTORE_STATUS.md`)
against a disposable container. That drill is **not** production RPO.

## Required on the production host

1. Continuous **off-host** WAL archive (object storage or the managed
   provider's PITR). WAL that lives only on the database volume is not
   an archive.
2. Measured RPO: write a canary row, wait N seconds, restore to a
   target just before a later disaster write, confirm the canary and
   the absence of the disaster row.
3. Scheduled restore drill (quarterly at minimum).

## Managed Postgres

If the platform is RDS / Cloud SQL / Crunchy / similar, enable the
provider PITR window and record:

- retention (hours/days)
- last successful restore drill date
- measured RPO from that drill

Do not mark P1-10-PROD closed until those three exist.

## What not to do

Do not treat `pg_dump` alone as PITR. Do not commit WAL files.
