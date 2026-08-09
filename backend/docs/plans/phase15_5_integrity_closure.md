# Phase 15.5 — Cross-Cutting Integrity Closure

**Status:** IN REVIEW on PR #25 — **15.5B review fixes applied**  
**Base:** main `af8f809` (Phase 8–15 LOCKED)  
**Blocks:** Phase 16 Notifications / Reports  
**Migrations:** `n7a8b9c0d1e2` + `o8b9c0d1e2f3`

## Goal

Close cross-phase integrity gaps **without reopening** Phase 8–15 product scope.

## Scope + evidence (15.5 + 15.5B)

| # | Item | Evidence |
|---|------|----------|
| 1 | RBAC least privilege | MEMBER: no tenant-wide `members:read` / `access:issue`; `access:issue:self` + `/access/qr/issue-self` via `members.user_id`. Tenant roles lose `outbox:dispatch`. |
| 1b | YAML↔DB parity | `check_permissions_db.py` checks missing **and** extra grants; mutation test proves over-grant fails. |
| 2 | Idempotency atomic failure | Nested savepoint UoW; FAILED same-hash only. |
| 3 | Outbox lease + fencing | CAS `mark_published`/`mark_failed` on `worker_id`; stale worker denied. |
| 4 | Inbox retry + atomicity | Handler in nested savepoint; domain flushes roll back on failure. |
| 5 | Event envelope validation | `validate_envelope` for tenantid/type/data/id/specversion. |
| 6 | Finance immutability | Allocation reversals + DB triggers deny UPDATE/DELETE. |
| 7 | Entitlement ledger DoD | RESTRICT + triggers + PG negative tests. |
| 8 | Legacy Entitlement | Deprecation note (DROP later). |

## Dispatch safety

- Public `/outbox/dispatch` returns **404** unless `ALLOW_OUTBOX_NOOP_DISPATCH=true` (default false).
- Real workers must call `claim_pending` + publisher ACK + `mark_published(..., worker_id=...)`.

## Exit criteria

- [x] Hostile PG tests (fencing, inbox atomicity, finance/entitlement, RBAC)
- [x] `alembic check` clean
- [ ] CI green after 15.5B push
- [ ] Human review/approve — **no protection bypass**
- [ ] Merge + main CI → Phase 16

## Terminology

**At-least-once delivery + idempotent/deduped consumers → effectively-once business effects.**  
Do not claim global exactly-once.
