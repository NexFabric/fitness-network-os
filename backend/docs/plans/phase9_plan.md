# Phase 9: Entitlement & Resolution Engine

**Status: 🟢 COMPLETED / CI VERIFIED / LOCKED (merged main via PR #14)**  
**Supersedes:** earlier “terms_snapshot boolean only” draft narrative.  
**Note (2026-08-09):** Phase 12–15 also LOCKED; global idempotency + QR access delivered.

## Goal

Phase 8 delivered membership lifecycle, plan versions, and period invariants.  
Phase 9 makes rights **actionable** via:

1. **Resolution Engine** — time-based transitions (SCHEDULED→ACTIVE, renewals, expirations).
2. **Entitlement Engine** — Definition / PlanVersion mapping / Membership snapshot / Wallet / Ledger with real consume.

## Domain model

```text
PlanVersion (immutable)
  └── PlanEntitlement[] → EntitlementDefinition
Membership (ACTIVE…)
  └── MembershipEntitlement[] (snapshot)
        └── EntitlementWallet (allocated/reserved/consumed/remaining)
              └── EntitlementTransaction (append-only, UNIQUE tenant+idempotency_key)
```

Kinds: `BOOLEAN`, `COUNT`.

Ledger types: `ALLOCATE`, `RESERVE`, `RELEASE`, `CONSUME`, `ADJUST`, `EXPIRE`, `REVERSE`  
(Phase 9 implements ALLOCATE + CONSUME; others reserved).

## APIs

- `POST /api/v1/members/{member_id}/entitlements/check` — no mutation; `entitlements:check`
- `POST /api/v1/members/{member_id}/entitlements/consume` — mutates wallet; requires `Idempotency-Key`; `entitlements:consume`

## Permissions

`entitlements:read|check|consume|manage` seeded and mapped per role (see `permissions.yml`).

## Resolution

`ResolutionEngine.run_for_tenant(tenant_id)`:

1. `set_config('app.current_tenant_id', …, true)`
2. Activate scheduled memberships (also allocates wallets via MembershipService)
3. Process PENDING renewals (snapshots + period roll + allocate)
4. Expire ACTIVE/PAST_DUE past end_date (closes period)

Failure isolation: per-item `begin_nested()` savepoints.

## Tenancy

All new tables: `tenant_id`, composite FKs, indexes, **ENABLE + FORCE RLS**.

## Tests (required)

- Zero balance / insufficient
- Check does not mutate
- Consume success + ledger
- Idempotent replay
- Concurrent double-consume (two sessions, remaining=1 → one success)
- BOOLEAN grant
- Tenant RLS isolation via `app_user`
- Permission ALLOW/DENY
- Resolution activate / renew / expire / error isolation / multi-tenant

## Deferred

- Full RESERVE/RELEASE booking product UX
- Global Phase 12 Idempotency middleware store
- Phase 13 QR / Access Decision
- Phase 10 Finance
