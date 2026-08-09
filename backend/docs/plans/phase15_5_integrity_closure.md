# Phase 15.5 — Cross-Cutting Integrity Closure

**Status:** IN PROGRESS (`feat/phase15-5-integrity-closure`)  
**Base:** main `af8f809` (Phase 8–15 LOCKED)  
**Blocks:** Phase 16 Notifications / Reports

## Goal

Close cross-phase integrity gaps **without reopening** Phase 8–15 product scope. Single hardening PR.

## Scope (exact)

| # | Item | Deliverable |
|---|------|-------------|
| 1 | RBAC SoT drift | `permissions.yml` = runtime grants; CI DB↔YAML parity |
| 2 | Idempotency atomic failure | Business savepoint; partial rollback; FAILED same-hash retry only |
| 3 | Outbox crash recovery | `worker_id` + `lease_until`; stale PROCESSING reclaim |
| 4 | Inbox retry | `available_at` + FAILED/DEAD backoff (effectively-once language) |
| 5 | Event Envelope v1 | Shared envelope builder for outbox producers |
| 6 | Finance allocation reversal | Append-only reversals; no mutate/delete allocations |
| 7 | Entitlement ledger | Wallet FK RESTRICT; deny UPDATE/DELETE triggers |
| 8 | Legacy Entitlement | Deprecation note + usage=0 plan (no DROP this rev) |

## Explicitly deferred (Phase 16–26)

- Full MFA / auth routers, KMS QR, offline gateway  
- Audit DB role lockdown (beyond app triggers where done)  
- Notification/Report product (Phase 16)  
- Container / CORS / observability  

## Exit criteria

- Real PG tests for each of 1–7  
- `alembic check` clean  
- CI green including permissions DB parity after migrate  
- Docs: Phase 15.5 LOCKED path before Phase 16  

## Terminology

Outbox/Inbox: **at-least-once delivery + idempotent/deduped consumers → effectively-once business effects**. Avoid global “exactly-once” claims.
