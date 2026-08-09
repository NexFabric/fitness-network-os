# Phase 15.6 — Residual Closeout / Post-Integrity Ops Polish

**Status:** 🟢 **DONE on branch** (`feat/phase16-notifications-reports` stack) — **not LOCKED**  
**Date:** 2026-08-10  
**Depends on:** Phase 15.5 PR [#25](https://github.com/NexFabric/fitness-network-os/pull/25) (CI green; formal APPROVE + merge still open)  
**Carried with:** Phase 16 PR [#26](https://github.com/NexFabric/fitness-network-os/pull/26) (stacked on 15.5)

## What 15.6 is

Minimal residual after Phase **15.5 Integrity Closure** and the Phase **16** integrity review:

| # | Item | Severity | Disposition |
|---|------|----------|-------------|
| 1 | Document `process_due_failed` as a **required ops job** before production notification delivery | P2 / ops | **DONE** (this doc + checklist) |
| 2 | HTTP **201** when delivery/run is created; **200** on dedupe hit (`created=False`) | P2 (IR-001 / P16-014) | **DONE** in endpoints + API test |
| 3 | Checklist truth: 15.6 residual **DONE on branch**, never false **LOCKED** | process | **DONE** |

## What 15.6 is not

- Not a reopening of Phase 8–15 product scope  
- Not a substitute for Phase 15.5 human APPROVE / merge / main CI  
- Not a claim of **LOCKED**, **CI VERIFIED on main**, or **production-ready**  
- Not a full worker/cron productization (standalone scheduler remains deferred)

## Evidence

### Ops — `NotificationService.process_due_failed`

**Required before production notification delivery reliability claims:**

| Field | Value |
|-------|--------|
| Method | `NotificationService.process_due_failed(tenant_id, limit=…)` |
| Purpose | Claim tenant-scoped `FAILED` deliveries with `available_at <= now` and `attempt_count < max_attempts` (`SKIP LOCKED`); re-dispatch without public inbox inject |
| Why required | Outbox path keeps retry alive when the handler **raises** on non-SENT. Deliveries that land in `FAILED` after provider failure also need this dual path when not re-driven solely by outbox. Without a scheduled/ops job calling this method, some failed deliveries can stall until manual intervention. |
| Topology (MVP) | **Per-tenant** job (or operator loop over tenants). Index `ix_notification_deliveries_available` is `(status, available_at)` — fine for tenant-scoped workers. Platform-wide multi-tenant worker is a later index/API change (P16-013). |
| Surface today | Service method + unit/integration tests + **ops CLI** `scripts/process_notification_due.py`. **No** public HTTP route, **no** product cron scheduler — intentional MVP. |
| Production gate | Wire cron / worker / ops runbook to invoke `process_due_failed` (or the CLI below) **before** claiming production notification reliability. |

**How to run (ops CLI):**

```bash
# from backend/, DATABASE_URL (and env) loaded as for the app
uv run python scripts/process_notification_due.py <tenant_uuid>
uv run python scripts/process_notification_due.py <tenant_uuid> --limit 50 --max-attempts 5
```

Stdout is one JSON line, e.g. `{"tenant_id":"…","sent":1,"failed":0,"dead":0}`.  
Per-tenant only (loop tenants in the scheduler if multi-tenant). Do **not** expose this as a public HTTP endpoint.

**Deferred (not 15.6):** standalone worker process, multi-tenant global claim API, real provider SDKs.

### API consistency — dedupe status codes

| Endpoint | First create | Dedupe hit |
|----------|--------------|------------|
| `POST /api/v1/notifications/deliveries` | **201** + `created: true` | **200** + `created: false` |
| `POST /api/v1/reports/runs` | **201** + `created: true` | **200** + `created: false` |

Body always includes `created` for clients that ignore status codes. Templates/definitions create paths remain fixed **201**.

### Tests

- Service: existing `test_schedule_delivery_dedupe_key_idempotent` / `test_request_run_dedupe_key_idempotent`  
- API: `test_delivery_and_run_dedupe_returns_200` (HTTP 201 then 200)

## Merge / lock rules

```text
main (Phase 8–15 LOCKED)
  → Phase 15.5 PR #25 APPROVE + merge + main CI → 15.5 LOCKED
  → Phase 16 PR #26 (includes 15.6 residual) merge + main CI → 16 LOCKED
  → Only then may checklist claim CI VERIFIED / LOCKED for 15.6/16
```

**Formal blocker (process only):** PR #25 is MERGEABLE and CI green but `reviewDecision=REVIEW_REQUIRED`.  
`gh pr merge 25 --merge` and `gh pr merge 25 --admin --merge` both fail without an independent approving review.  
Do **not** weaken branch protection permanently. Do **not** force-push main.

## Residual P2 (post reliability batch on Phase 16 branch)

From integrity reviews — status on `feat/phase16-notifications-reports`:

- IR-002/003 / P16-011: report `FAILED` redrive / terminal handling — **CLOSED** (raise on FAILED; `redrive=` flag)  
- IR-004: free-form `recipient_address` staff policy — **CLOSED** (address-only → `notifications:write`)  
- IR-006/007: dual handlers / DEAD raises — **CLOSED** (shared parse; DEAD/CANCELLED success)  
- IR-005: `process_due_failed` surface — **MITIGATED** (ops CLI; product cron deferred)  
- P16-010: model vs migration partial unique index parity — still open (docs/hygiene)  
- Domain → notification bridges — **helper landed** (`NotificationBridge`; not wired into MembershipService)  
- Full deep RLS suite optional — isolation suite present; further depth deferred

## Terminology

Do **not** mark Phase 15.6 **LOCKED** on this document alone.  
**DONE on branch** = implemented + tested on stacked feature branch.  
**LOCKED** = merge to `main` + required CI green + honest checklist update.
