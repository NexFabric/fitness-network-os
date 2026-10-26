# Disaster Recovery / Restore — Status

**Date:** 2026-08-16
**Status:** **DUMP/RESTORE + PITR DRILLS EXECUTED & VERIFIED**

Two different drills, because they prove different things:

| Drill | Script | Proves |
|---|---|---|
| Dump / restore | `backend/scripts/dr_restore_drill.sh` | A backup can be taken and fully restored with row/RLS parity |
| **Point-in-time recovery** | `backend/scripts/pitr_drill.sh` | WAL replay can rewind to a moment **before** an operator mistake |

A dump/restore round-trip is not PITR — it cannot undo a bad `DELETE` that
happened after the last dump. The PITR drill below closes that gap.

## Target (PRODUCTION_READINESS)

| Metric | Target | Measured in Drill |
|--------|--------|-------------------|
| RPO | ≤ 5 minutes | Point-in-time snapshot dump |
| RTO | ≤ 60 minutes | < 5 seconds (local/staging drill) |
| Access RTO | ≤ 15 minutes | Immediate |
| Restore tests | Monthly automated | Automated script `backend/scripts/dr_restore_drill.sh` |

## Drill Execution Evidence (2026-08-14)

- **Script:** [`backend/scripts/dr_restore_drill.sh`](file:///Users/emrah/GymClubNex/backend/scripts/dr_restore_drill.sh)
- **Source Database:** `fitness_os` (PostgreSQL 16)
- **Target Drill Database:** `fitness_os_dr_drill_*`
- **Dump Size:** 432 KB full schema + data
- **Integrity Checks Passed:**
  - Tenants count verified & matched: 2
  - Members count verified & matched: 9
  - Full relational schema + composite RLS policies verified intact
- **Result:** `=== DR RESTORE DRILL PASSED SUCCESSFULLY ===`

## Re-run Evidence — Dump/Restore (2026-08-16)

```
Dump file size: 632K
Backup SHA256:  963248d430b9d9579a7c2d0bf0d6b237c02e7c116b7670e66ad7d44ee7109f8b
 - Tenants count: 8
 - Members count: 33
 - RLS-enabled tables: 72
=== DR RESTORE DRILL PASSED SUCCESSFULLY ===
```

## PITR Drill Evidence (2026-08-16) — `backend/scripts/pitr_drill.sh`

Runs against a throwaway `postgres:16` container (the dev database is never
touched) with `wal_level=replica`, `archive_mode=on` and a real WAL archive.

Scenario: base backup → write `keep-me` → record recovery target time → write
`disaster-drop-table` → restore base backup → replay WAL to the target.

```
archive_mode=on confirmed
base backup      : pg_basebackup -Fp -Xs
recovery target  : 2026-08-16 13:38:27.741663+00
rows before      : 2 (keep-me, disaster-drop-table)
rows after       : 1 (keep-me)
disaster row     : correctly absent
pg_stat_archiver : archived=6 failed=0
=== PITR DRILL PASSED ===
```

The post-recovery instance promoted out of recovery (`pg_is_in_recovery() = f`)
and contained exactly the committed state as of the target timestamp — the
write that happened after the target was correctly discarded.

### What the PITR drill does NOT close

- It runs on a **local throwaway container**, not the production database host.
- Production still needs **continuous WAL archiving to durable off-host
  storage** (S3/managed provider) plus a retention policy — the drill archives
  to a container-local directory.
- **RPO ≤ 5 min** is a configuration property of the production archive
  schedule (`archive_timeout` / managed provider snapshots), not something a
  local drill measures.

## Operational Requirements for Cloud Production

1. **Managed Provider Backups:** Enable continuous WAL archiving + daily automated snapshots on target DB host.
2. **Scheduled Drill:** Execute `dr_restore_drill.sh` on the 1st of every month via CI/cron to maintain certification.  
