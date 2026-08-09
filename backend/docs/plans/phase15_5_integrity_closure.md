# Phase 15.5 — Cross-Cutting Integrity Closure

**Status:** 🟢 **CI VERIFIED / LOCKED** on main merge `125a8c6` (PR [#25](https://github.com/NexFabric/fitness-network-os/pull/25)); lock docs PR [#27](https://github.com/NexFabric/fitness-network-os/pull/27)  
**Base at lock:** main `125a8c6` (docs lineage `f59f1f7`)  
**Unblocks:** Phase 16 Notifications / Reports (branch PR #26 — not LOCKED)  
**Migrations:** `n7a8b9c0d1e2` + `o8b9c0d1e2f3` + `p9c0d1e2f3a4` (head on main; 15.5D was code-only)

## Goal

Close cross-phase integrity gaps **without reopening** Phase 8–15 product scope.

## Scope + evidence (15.5 + 15.5B + 15.5C + 15.5D)

| # | Item | Evidence |
|---|------|----------|
| 1 | RBAC least privilege | MEMBER: no tenant-wide `members:read` / `access:issue` / domain reads; `*:self` + `/me/*` + `/access/qr/issue-self` via `members.user_id`. |
| 1b | YAML↔DB parity | `check_permissions_db.py` checks missing **and** extra grants. |
| 1c | **15.5C Event ingress** | Generic `POST /outbox/events` + `/outbox/inbox` **removed** from public API. GYM_* lack `outbox:*` / `inbox:*`. `OutboxService` in-process only. |
| 1d | **15.5C MEMBER BOLA** | MEMBER lacks `entitlements:check` etc.; has `entitlements:check:self` + `POST /me/entitlements/check`. Cross-member path DENY tests. |
| 1e | **15.5C/D event_type** | Pattern **and** canonical registry on enqueue; unknown well-formed types DENY. |
| 1f | **15.5D outbox max-attempts** | Claim filters `attempt_count < max`; stale exhausted PROCESSING → DEAD (`max_attempts_exceeded_on_claim`). |
| 1g | **15.5D *:self scope** | `is_authorized` requires owner for `*:self`; helpers `require_self` / `require_tenant`. |
| 2 | Idempotency atomic failure | Nested savepoint UoW; FAILED same-hash only. |
| 3 | Outbox lease + fencing | CAS `mark_published`/`mark_failed` on `worker_id`; stale worker denied. |
| 4 | Inbox retry + atomicity | Handler in nested savepoint; domain flushes roll back on failure. |
| 5 | Event envelope validation | `validate_envelope` for tenantid/type/data/id/specversion. |
| 6 | Finance immutability | Allocation reversals + DB triggers deny UPDATE/DELETE. |
| 7 | Entitlement ledger DoD | RESTRICT + triggers + PG negative tests. |
| 8 | Legacy Entitlement | Deprecation note (DROP later). |

## Dispatch / ingress safety

- Generic tenant HTTP outbox/inbox **removed** (15.5C).
- Provider webhooks (Phase 16+): signature → tenant from integration config → allowlist/normalize → `receive_inbox` → fast ACK → worker.
- Real workers call `claim_pending` + publisher ACK + `mark_published(..., worker_id=...)`.

## Deferred (not merge blockers; still open product work)

- TRAINER → ASSIGNED members only
- Standalone worker process
- Provider-specific webhook adapters
- Real notification transports (Phase 16+ adapters)

## Exit criteria

- [x] Hostile PG tests (fencing, crash-loop max-attempts, inbox atomicity, finance/entitlement, RBAC, BOLA, no public outbox, event registry)
- [x] `alembic check` clean (local after migrate)
- [x] PR CI green after 15.5D (`ffba0a8` — Security, Lint, Unit/Integration, CodeQL)
- [x] Independent human review/approve + merge to main
- [x] Main post-merge CI green (run on `125a8c6`)
- [x] Phase 15.5 **LOCKED** · alembic head `p9c0d1e2f3a4` → Phase 16 GO (branch)

## Terminology

**At-least-once delivery + idempotent/deduped consumers → effectively-once business effects.**  
Do not claim global exactly-once.

## Lock record

| Field | Value |
|-------|--------|
| PR | #25 |
| Merge SHA | `125a8c6` |
| Lock docs | PR #27 → `f59f1f7` |
| Alembic head | `p9c0d1e2f3a4` |
| Maturity | 🟢 CI VERIFIED / LOCKED |
| Production-ready | **No** (Phase 16–26 remaining; Phase 26 NOT PASSED) |
