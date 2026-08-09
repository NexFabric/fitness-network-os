# Review Checkpoint — After Phase 8–11

**Date:** 2026-08-09  
**Purpose:** Human review stop before Phase 12 (Idempotency Engine).

## Locked / CI verified on `main`

| Phase | PR | main merge | Status |
|-------|-----|------------|--------|
| Phase 8 Membership | [#13](https://github.com/NexFabric/fitness-network-os/pull/13) | yes | 🟢 LOCKED / CI VERIFIED |
| Phase 9 Entitlements | [#14](https://github.com/NexFabric/fitness-network-os/pull/14) | yes | 🟢 LOCKED / CI VERIFIED |
| Phase 10 Finance | [#15](https://github.com/NexFabric/fitness-network-os/pull/15) | yes | 🟢 LOCKED / CI VERIFIED |
| Phase 11 Money floats | [#17](https://github.com/NexFabric/fitness-network-os/pull/17) | **open** | 🟠 IMPLEMENTED — review/merge |

## Phase 11 PR #17 (review this next)

- Branch: `feat/phase11-remove-money-floats`
- Changes:
  - No money `Float` columns in ORM
  - `Opportunity.value` → `value_amount_minor` + `currency`
  - `churn_probability` → `churn_probability_bps`
  - CI fitness: `scripts/check_no_money_floats.py`
  - Money helpers: `app/core/money.py` (Decimal, rejects float)

## Do not start yet

- Phase 12 — Real Idempotency Engine  
- Phase 13+ (QR, Member core, Outbox, etc.)

## Suggested review focus

1. Finance ledger invariants (partial pay, refund, credit) — already on main  
2. Entitlement wallet/ledger + RLS — already on main  
3. Phase 11 money float removal + CI fitness gate — PR #17  
4. Branch protection still requires 1 approving review (authors cannot self-approve without temporary policy change)

## Local verification notes

- Postgres test DB often on Docker port **5433**  
- Full suite last local run (pre-review): 60–67 passed depending on suite contents after Phase 10/11

## After review

1. Merge PR #17 when green  
2. Confirm `main` CI green  
3. Mark Phase 11 🟢 CI VERIFIED in checklist  
4. Only then open Phase 12  
