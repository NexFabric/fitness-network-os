# Review Checkpoint — Phase 8–15 LOCKED on main · 15.5 merge gate open

**Date:** 2026-08-10  
**Purpose:** Single human-facing status of sequential locks; next lock is Phase 15.5 then Phase 16+.  
**Main HEAD (docs sync base):** `af8f809`  
**PR #25 head (15.5):** `ffba0a8`  
**Alembic head on 15.5 branch:** `p9c0d1e2f3a4` · on main still ends Phase 15 track until merge

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
| Head | `ffba0a8` (15.5 + B + C + D) |
| Code | P0 event ingress + MEMBER BOLA closed; P1 max-attempts / `*:self` / event registry closed |
| PR CI | 🟢 green (Security, Lint+mypy, Unit/Integration incl. tenancy + RBAC parity, CodeQL) |
| Independent human APPROVE | ❌ still required |
| Merged to main | ❌ |
| Phase 15.5 LOCKED | ❌ until merge + main CI green |

## Current position

- **Completed domain track on main:** Phase 8 → 15  
- **Active formal gate:** Phase **15.5** integrity closure — code complete on PR #25; **await APPROVE → merge → main CI → LOCKED docs**  
- **Then:** Phase **16** Notifications & Reports → 17 routers → 18 E2E → 19–26  

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
| Checklist | `docs/PROGRESS_CHECKLIST.md` |
| Roadmap | `docs/IMPLEMENTATION_MASTER_PLAN.md` |
