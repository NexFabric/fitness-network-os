# Phase 15.5 — Cross-Cutting Integrity Closure

**Status:** IN REVIEW on PR #25 — **15.5C trust boundary delta applied**  
**Base:** main `af8f809` (Phase 8–15 LOCKED)  
**Blocks:** Phase 16 Notifications / Reports  
**Migrations:** `n7a8b9c0d1e2` + `o8b9c0d1e2f3` + `p9c0d1e2f3a4`

## Goal

Close cross-phase integrity gaps **without reopening** Phase 8–15 product scope.

## Scope + evidence (15.5 + 15.5B + 15.5C)

| # | Item | Evidence |
|---|------|----------|
| 1 | RBAC least privilege | MEMBER: no tenant-wide `members:read` / `access:issue` / domain reads; `*:self` + `/me/*` + `/access/qr/issue-self` via `members.user_id`. |
| 1b | YAML↔DB parity | `check_permissions_db.py` checks missing **and** extra grants. |
| 1c | **15.5C Event ingress** | Generic `POST /outbox/events` + `/outbox/inbox` **removed** from public API. GYM_* lack `outbox:*` / `inbox:*`. `OutboxService` in-process only. |
| 1d | **15.5C MEMBER BOLA** | MEMBER lacks `entitlements:check` etc.; has `entitlements:check:self` + `POST /me/entitlements/check`. Cross-member path DENY tests. |
| 1e | **15.5C event_type** | `domain.action.vN` pattern enforced on enqueue (`app.core.event_types`). |
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

## Deferred (not merge blockers)

- TRAINER → ASSIGNED members only
- Full `/me/memberships` + `/me/checkins` product surface (perms exist; routes later)
- Standalone worker process
- Provider-specific webhook adapters

## Exit criteria

- [x] Hostile PG tests (fencing, inbox atomicity, finance/entitlement, RBAC, BOLA, no public outbox)
- [x] `alembic check` clean (local after migrate)
- [ ] CI green after 15.5C push
- [ ] Independent human review/approve — **no protection bypass / no self-APPROVE as formal gate**
- [ ] Merge + main CI → Phase 15.5 LOCKED → Phase 16 GO

## Terminology

**At-least-once delivery + idempotent/deduped consumers → effectively-once business effects.**  
Do not claim global exactly-once.
