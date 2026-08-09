# Review Checkpoint — Phase 8–15.5 LOCKED on main · Phase 16+ active on branch

**Date:** 2026-08-10  
**Purpose:** Single human-facing status of sequential locks; next locks are Phase 16+ after their own merge gates.  
**Main HEAD:** `125a8c6` (Phase 15.5 integrity merge)  
**Alembic head on main:** `p9c0d1e2f3a4`  
**Active stack:** `feat/phase16-notifications-reports` / PR [#26](https://github.com/NexFabric/fitness-network-os/pull/26) (base `main`)

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
| Phase 15.5 Integrity | [#25](https://github.com/NexFabric/fitness-network-os/pull/25) | `125a8c6` | 🟢 **LOCKED / CI VERIFIED** |

## Phase 15.5 — LOCKED summary

| Item | Status |
|------|--------|
| PR | [#25](https://github.com/NexFabric/fitness-network-os/pull/25) · branch `feat/phase15-5-integrity-closure` |
| Main merge | `125a8c6` |
| Alembic head | `p9c0d1e2f3a4` |
| Code | P0 event ingress + MEMBER BOLA closed; P1 max-attempts / `*:self` / event registry closed |
| Status | 🟢 **CI VERIFIED / LOCKED** on main |

## Not locked (branch / next gates)

| Band | Status |
|------|--------|
| Phase 16–20 | 🟡 feature branch PR #26 only — **do not mark LOCKED** |
| Phase 21–23 | ⬜ starting (CI V2 frontend jobs + container/HTTP security plans) |
| Phase 24–26 | ⬜ not started |

## Current position

- **Completed on main:** Phase 0–7 gate + Phase 8–15 domain + **Phase 15.5 integrity**  
- **Active development:** Phase **16–20** stack (notifications/reports → routers → E2E → admin/scanner) on PR #26  
- **Next hardening track:** Phase **21** CI V2 → 22 container → 23 HTTP security baseline  

## Explicitly not production-ready

- Phase 16–26 incomplete / not LOCKED  
- Money float **CONTRACT** DROP deferred  
- KMS QR secrets, offline gateway, real notification transports deferred  
- No CORE MVP EXIT GATE (Phase 26)  

## Local verification notes

- Postgres test DB often on Docker port **5433** (`TEST_DATABASE_URL`)  
- Full suite scale after 15.5D: ~187 unit/integration tests on main (e2e ignored until Phase 18 branch)  

## Plan index

| Phase | Path |
|-------|------|
| 9 | `backend/docs/plans/phase9_plan.md` |
| 11 | `docs/plans/phase11_money_floats.md` |
| 12–15 | `backend/docs/plans/phase12_idempotency.md` … `phase15_outbox_inbox.md` |
| 15.5 | `backend/docs/plans/phase15_5_integrity_closure.md` |
| Checklist | `docs/PROGRESS_CHECKLIST.md` |
| Roadmap | `docs/IMPLEMENTATION_MASTER_PLAN.md` |
