# Review Checkpoint — After Phase 8–11

**Date:** 2026-08-09  
**Purpose:** Human review stop before Phase 12 (Idempotency Engine).

## Locked / CI verified on `main`

| Phase | PR | main merge | Status |
|-------|-----|------------|--------|
| Phase 8 Membership | [#13](https://github.com/NexFabric/fitness-network-os/pull/13) | yes | 🟢 LOCKED / CI VERIFIED |
| Phase 9 Entitlements | [#14](https://github.com/NexFabric/fitness-network-os/pull/14) | yes | 🟢 LOCKED / CI VERIFIED |
| Phase 10 Finance | [#15](https://github.com/NexFabric/fitness-network-os/pull/15) | yes | 🟢 LOCKED / CI VERIFIED |
| Phase 11 Money floats | [#17](https://github.com/NexFabric/fitness-network-os/pull/17) | **open** | 🟠 CLOSING — expand-only + strict money |

## Phase 11 PR #17 (merge after CI)

- Branch: `feat/phase11-remove-money-floats`
- Closure items (review findings):
  - **EXPAND** migration only (legacy float columns kept until CONTRACT)
  - Historical Opportunity currency assumption: **TRY**
  - Conversion tests (major string → minor, bps)
  - StrictInt money at API + `assert_amount_minor` in services
  - EntitlementService flushes only (API commits) — Phase 12 UoW prep
  - Docs: IMPLEMENTATION_MASTER_PLAN + phase11 plan
- Deferred CONTRACT: `g8b9c0d1e2f3` no-op placeholder until dual-column window ends

## Do not start yet

- Phase 12 — Real Idempotency Engine (until Phase 11 LOCKED on main)  
- Phase 13+ (QR, Member core, Outbox, etc.)

## Suggested review focus

1. Expand/contract correctness (no DROP in expand rev)  
2. Strict money coercion rejection  
3. Finance ledger audit debt (allocation mutation on refund) — P1 later  
4. Legacy `Entitlement` model deprecation — before Phase 13

## Local verification notes

- Postgres test DB often on Docker port **5433**  
- Full suite last local run (pre-review): 60–67 passed depending on suite contents after Phase 10/11

## After review

1. Merge PR #17 when green  
2. Confirm `main` CI green  
3. Mark Phase 11 🟢 CI VERIFIED in checklist  
4. Only then open Phase 12  
