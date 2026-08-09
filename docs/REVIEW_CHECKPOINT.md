# Review Checkpoint — Phase 8–15 LOCKED on main · 15.5 merge gate open

**Date:** 2026-08-10  
**Purpose:** Single human-facing status of sequential locks; next lock is Phase 15.5 then Phase 16+.  
**Main HEAD (docs sync base):** `af8f809`  
**PR #25 (15.5):** open · CI green · **REVIEW_REQUIRED** (no self-APPROVE)  
**PR #26 (16):** open · base `feat/phase15-5-integrity-closure` · integrity **CLEAN** on branch · **not merge-ahead of 15.5**  
**Alembic:** 15.5 `p9c0d1e2f3a4` · 16 branch `q0d1e2f3a4b5`

## Locked / CI verified on `main`

| Phase | PR | main merge | Status |
|-------|-----|------------|--------|
| Phase 8 Membership | [#13](https://github.com/NexFabric/fitness-network-os/pull/13) | yes | 🟢 LOCKED / CI VERIFIED |
| Phase 9 Entitlements | [#14](https://github.com/NexFabric/fitness-network-os/pull/14) | yes | 🟢 LOCKED / CI VERIFIED |
| Phase 10 Finance | [#15](https://github.com/NexFabric/fitness-network-os/pull/15) | yes | 🟢 LOCKED / CI VERIFIED |
| Phase 11 Money floats | [#17](https://github.com/NexFabric/fitness-network-os/pull/17) | `607b087` | 🟢 LOCKED / CI VERIFIED |
| Phase 11 lock docs | [#18](https://github.com/NexFabric/fitness-network-os/pull/18) | yes | 🟢 docs |
| Phase 12 Idempotency | [#19](https://github.com/NexFabric/fitness-network-os/pull/19) | `227f42e` | 🟢 LOCKED / CI VERIFIED |
| Phase 13 QR & Access | [#20](https://github.com/NexFabric/fitness-network-os/pull/20) | `babc33c` | 🟢 LOCKED / CI VERIFIED |
| Phase 14 Member/Gym | [#21](https://github.com/NexFabric/fitness-network-os/pull/21) | `e332cf5` | 🟢 LOCKED / CI VERIFIED |
| Phase 15 Outbox/Inbox | [#22](https://github.com/NexFabric/fitness-network-os/pull/22) | `67b8214` | 🟢 LOCKED / CI VERIFIED |
| Phase 15 lock docs | [#23](https://github.com/NexFabric/fitness-network-os/pull/23) | `af8f809` lineage | 🟢 docs |

## Phase 15.5 — open merge gate (not LOCKED)

| Item | Status |
|------|--------|
| PR | [#25](https://github.com/NexFabric/fitness-network-os/pull/25) · branch `feat/phase15-5-integrity-closure` |
| Head | includes 15.5B/C/D + docs truth sync |
| Code | P0 event ingress + MEMBER BOLA closed; P1 max-attempts / `*:self` / event registry closed |
| PR CI | 🟢 green |
| Independent human APPROVE | ❌ still required (GitHub blocks self-APPROVE) |
| Merged to main | ❌ |
| Phase 15.5 LOCKED | ❌ until merge + main CI green |

## Phase 16 — stacked WIP (not LOCKED)

| Item | Status |
|------|--------|
| PR | [#26](https://github.com/NexFabric/fitness-network-os/pull/26) |
| Integrity review | **CLEAN** (`backend/docs/plans/INTEGRITY_REVIEW_phase16_closeout.md`) |
| Local focused suite | 78 passed (notifications/reports/tenancy/API/arch/event/rbac) |
| Merge | Only **after** 15.5 LOCKED on `main` (then rebase/retarget if needed) |

## Current position

- **Completed domain track on main:** Phase 8 → 15  
- **Formal gate #1:** Phase **15.5** PR #25 — APPROVE → merge → main CI → LOCKED  
- **Parallel code track:** Phase **16** PR #26 prepared (stacked); do not merge before 15.5  
- **Then:** Phase 17 routers → 18 E2E → 19–26  

## Explicitly not production-ready

- Phase 16–26 incomplete  
- Money float **CONTRACT** DROP deferred  
- KMS QR secrets, offline gateway, real notification transports deferred  
- No CORE MVP EXIT GATE (Phase 26)  

## Local verification notes

- Postgres test DB often on Docker port **5433** (`TEST_DATABASE_URL`)  
- Full suite scale after 15.5D: ~187 unit/integration tests (e2e ignored)  

## Plan index

| Phase | Path |
|-------|------|
| 9 | `backend/docs/plans/phase9_plan.md` |
| 11 | `docs/plans/phase11_money_floats.md` |
| 12–15 | `backend/docs/plans/phase12_idempotency.md` … `phase15_outbox_inbox.md` |
| 15.5 | `backend/docs/plans/phase15_5_integrity_closure.md` |
| 16 | `backend/docs/plans/phase16_notifications_reports.md` |
| 16 integrity | `backend/docs/plans/INTEGRITY_REVIEW_phase16_closeout.md` |
| Checklist | `docs/PROGRESS_CHECKLIST.md` |
| Roadmap | `docs/IMPLEMENTATION_MASTER_PLAN.md` |
