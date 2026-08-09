# Review Checkpoint — Phase 8–15 LOCKED on main · 15.5 merge gate open · 16–20 on branch

**Date:** 2026-08-10  
**Purpose:** Single human-facing status of sequential locks; next lock is Phase 15.5 then Phase 16+.  
**Main HEAD (docs sync base):** `af8f809`  
**PR #25 (15.5):** open · CI green · **REVIEW_REQUIRED** (no self-APPROVE)  
**PR #26 / stack branch (`feat/phase16-notifications-reports`):** Phase **16–20 IMPLEMENTED on branch** · integrity **CLEAN** for 16 · **not LOCKED** · **not merge-ahead of 15.5**  
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
| PR / branch | [#26](https://github.com/NexFabric/fitness-network-os/pull/26) · `feat/phase16-notifications-reports` |
| Integrity review | **CLEAN** (`backend/docs/plans/INTEGRITY_REVIEW_phase16_closeout.md`) |
| Residual P2 + ops CLI + bridge | **CLOSED on branch** |
| Merge | Only **after** 15.5 LOCKED on `main` (then rebase/retarget if needed) |

## Phase 17–20 — IMPLEMENTED on branch (not LOCKED)

| Phase | Status | Pointer |
|-------|--------|---------|
| 17A `/me/*` | 🟠 on branch | `me.py` · `tests/api/test_me_self_service.py` · plan `phase17_api_v1_completion.md` |
| 18 E2E slice | 🟠 on branch | `tests/e2e/test_vertical_slice_*.py` · `phase18_vertical_slice_e2e.md` |
| 19 Admin Web | 🟠 on branch | `frontend/admin-web` · `phase19_admin_web.md` |
| 20 Scanner PWA | 🟠 on branch | `frontend/scanner-pwa` · `phase20_scanner_pwa.md` |
| Standing review | honest | `backend/docs/plans/STANDING_REVIEW_latest.md` |

## Current position

- **Completed domain track on main:** Phase 8 → 15  
- **Formal gate #1:** Phase **15.5** PR #25 — APPROVE → merge → main CI → LOCKED  
- **Parallel code track:** Phase **16–20** on `feat/phase16-notifications-reports`; do not merge before 15.5  
- **Then:** CI/merge 16–20 → Phase 21–26  

## Explicitly not production-ready

- Phase 15.5–26 not LOCKED / incomplete exit gate  
- Money float **CONTRACT** DROP deferred  
- KMS QR secrets, offline gateway, real notification transports deferred  
- No CORE MVP EXIT GATE (Phase 26)  

## Local verification notes

- Postgres test DB often on Docker port **5433** (`TEST_DATABASE_URL`)  
- 17A + 15.5c + e2e focused: 15 passed (2026-08-10)  
- Frontend: admin-web + scanner-pwa `npm run build` green  

## Plan index

| Phase | Path |
|-------|------|
| 9 | `backend/docs/plans/phase9_plan.md` |
| 11 | `docs/plans/phase11_money_floats.md` |
| 12–15 | `backend/docs/plans/phase12_idempotency.md` … `phase15_outbox_inbox.md` |
| 15.5 | `backend/docs/plans/phase15_5_integrity_closure.md` |
| 16 | `backend/docs/plans/phase16_notifications_reports.md` |
| 16 integrity | `backend/docs/plans/INTEGRITY_REVIEW_phase16_closeout.md` |
| 17 | `backend/docs/plans/phase17_api_v1_completion.md` |
| 18 | `backend/docs/plans/phase18_vertical_slice_e2e.md` |
| 19 | `backend/docs/plans/phase19_admin_web.md` |
| 20 | `backend/docs/plans/phase20_scanner_pwa.md` |
| Standing | `backend/docs/plans/STANDING_REVIEW_latest.md` |
| Checklist | `docs/PROGRESS_CHECKLIST.md` |
| Roadmap | `docs/IMPLEMENTATION_MASTER_PLAN.md` |
