# Rollback

Schema is expand-then-contract (PRODUCTION_READINESS ADR-037). A bad
application revision is rolled back by **redeploying the previous image
tag**. Do **not** run `alembic downgrade` as the default recovery.

## Application rollback

1. Keep the last known-good image digest (`fitness-network-os:<sha>`).
2. Stop the new backend/workers.
3. Start the previous image. Workers must match the backend revision.
4. Run `ops/deploy/smoke.sh`.
5. Leave the newer migration in place if it is backward-compatible.

## When a migration is not backward-compatible

Do not ship a destructive CONTRACT in the same release as the code
that still reads the old shape. If that rule was broken:

1. Restore from PITR / base backup (see `docs/ops/DR_RESTORE_STATUS.md`
   and `docs/ops/WAL_ARCHIVE.md`).
2. Treat this as an incident, not a routine rollback.

## What this file is not

A tested production rehearsal. Until a real host records a rollback
drill, status is **procedure landed · NOT VERIFIED**.
