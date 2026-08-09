# Independent Review — Phase 15.5 + Phase 16

**Branch:** `feat/phase16-notifications-reports` (includes 15.5 commits + Phase 16)  
**Reviewer role:** Independent code review (read-only assessment)  
**Date:** 2026-08-10  
**Scope:**  
1. Phase 15.5C/D trust boundaries (no public outbox, MEMBER `*:self`, event registry, outbox max-attempts)  
2. Phase 16 notifications/reports models, services, APIs, migration `q0d1e2f3a4b5`, permissions  

**Not in scope:** Implementing fixes; formal product sign-off; claiming production-ready.

---

## Verdicts

| Track | Verdict | Notes |
|-------|---------|--------|
| **Phase 15.5 code quality** | **READY_FOR_CI** (already PR CI green per docs) | Trust-boundary implementation is coherent and test-backed. |
| **Phase 15.5 formal merge gate** | **BLOCKED on process** | Requires **independent human APPROVE** on PR [#25](https://github.com/NexFabric/fitness-network-os/pull/25) → merge → main CI green → LOCKED docs. Code review ≠ formal APPROVE. |
| **Phase 16 branch** | **NEEDS_WORK** | Prior P0 contract/seed breakages appear fixed. Remaining P1 gaps (API/RBAC/RLS tests, schedule abuse surface, client `enqueue_outbox`) block calling the branch CI-merge-ready. |
| **Merge order** | **Process BLOCK** for Phase 16 | Do **not** merge Phase 16 to `main` until Phase 15.5 is **LOCKED**. Stacked branch work is OK. |

**Overall branch readiness for Phase 16 merge:** **NEEDS_WORK** (not `READY_FOR_CI`, not contract-`BLOCKED`).

---

## Phase 15.5 formal gate (separate from code quality)

| Item | Status |
|------|--------|
| Public `/api/v1/outbox/*` absent; `api.py` comment + 404 tests | ✅ Code |
| GYM_* lack `outbox:*` / `inbox:*` in `permissions.yml` | ✅ Code |
| MEMBER `*:self` + `require_self` / `require_tenant` | ✅ Code |
| `/me/entitlements/check` ownership via `members.user_id` | ✅ Code + API test |
| Event type pattern + registry on `OutboxService.enqueue` | ✅ Code |
| Outbox max-attempts → DEAD on claim / crash-loop | ✅ Code + tests |
| PR #25 human APPROVE + merge + main CI → LOCKED | ❌ **Open process gate** |

This review **does not** constitute formal APPROVE for Phase 15.5.

---

## Findings table

| ID | Sev | Finding | Path | Fix recommendation |
|----|-----|---------|------|--------------------|
| R-001 | **P1** | **16E API/RBAC surface untested.** Endpoints use `AuthorizationService.require_tenant` for `notifications:*` / `reports:*`, but there are **no** HTTP tests asserting MEMBER 403, FRONT_DESK cannot `notifications:write`, ACCOUNTANT cannot `notifications:send`, or happy-path staff 201. Service tests only. Plan 16E explicitly requires RBAC API coverage. | `app/api/v1/endpoints/notifications.py` (`create_template`, `schedule_delivery`, …); `app/api/v1/endpoints/reports.py`; missing `tests/api/test_notifications.py`, `tests/api/test_reports.py` | Add ASGI/httpx tests mirroring `test_phase15_5c_trust_boundaries.py`: MEMBER → 403 on all `/notifications/*` and `/reports/*`; role matrix samples; authn 401 without token. |
| R-002 | **P1** | **No hostile RLS / cross-tenant isolation tests** for Phase 16 tables. Services filter `tenant_id`, and tables have RLS from operational MVP, but plan 16E requires cross-tenant isolation on templates/deliveries/definitions/runs. A wrong query without `tenant_id` would only be caught by RLS + tests. | `NotificationService.*`, `ReportService.*`; missing PG RLS tests under `tests/` | Add PG tests: two tenants; set `app.current_tenant_id` for A; assert B’s deliveries/runs/templates invisible; optional direct SQL under wrong GUC. |
| R-003 | **P1** | **Client-controlled `enqueue_outbox` on public HTTP.** `DeliveryScheduleRequest.enqueue_outbox` and `RunRequest.enqueue_outbox` default `True` but are client-settable. Client can force `False` → `PENDING` delivery / run with **no** outbox row and **no** HTTP path to `dispatch_delivery` / `execute_run` (silent stuck work). | `endpoints/notifications.py` (`schedule_delivery`); `endpoints/reports.py` (`request_run`); service flags in `NotificationService.schedule_delivery`, `ReportService.request_run` | Drop field from public schemas; always enqueue on HTTP. Keep `enqueue_outbox` service-internal for unit tests only. |
| R-004 | **P1** | **Free-form recipient schedule is an abuse / spam vector.** `schedule_delivery` only requires `recipient_address` **or** `recipient_user_id`. No proof that address/user belongs to the tenant (or to a member). `recipient_user_id` FK is global `users.id` (non-composite). `notifications:send` is granted to **FRONT_DESK** → any desk staff can target arbitrary emails/phones/user UUIDs. Not classic member BOLA, but production send-API risk. | `NotificationService.schedule_delivery`; `NotificationDelivery.recipient_user_id`; `endpoints/notifications.py` | Resolve recipient from tenant-owned Member / contact record; reject unbound addresses on public API (or restrict free-form to GYM_OWNER/ADMIN / internal services). Validate `recipient_user_id` has a role or member bind in tenant. |
| R-005 | **P1** **CLOSED** | **Event type plan vs registry drift (docs-aligned).** Code truth remains multi-segment **`report.run.requested.v1`** (`REPORT_RUN_REQUESTED_V1`). Plan/docs updated to the same string (no production constant rename). Pattern multi-segment (`domain(.segment)+.vN`); enqueue + registry agree. | `app/core/event_types.py` (`REPORT_RUN_REQUESTED_V1`); `docs/plans/phase16_notifications_reports.md` | **CLOSED:** docs aligned to multi-segment `report.run.requested.v1` (code as source of truth). |
| R-006 | **P1** | **Architecture fitness gap for domain boundary.** Membership does not import providers (manual inspection OK), but plan 16E requires an architecture test forbidding Membership → notification providers / WhatsApp adapters. Current `test_architecture.py` only checks core→api and models→core/api. | `app/services/membership.py` (clean); `tests/test_architecture.py` | Add AST/import scan: `app/services/membership.py` must not import `app.services.notification_providers` (and preferably not channel SDKs). |
| R-007 | **P1** | **Delivery retry after outbox ACK depends on unscheduled `process_due_failed`.** `outbox_notification_requested_handler` always completes successfully after `dispatch_delivery`, even when status is `FAILED`/`DEAD`. `OutboxService.dispatch_claimed` then `mark_published`. Retry is only via `NotificationService.process_due_failed` (SKIP LOCKED) — **no worker, cron, or HTTP ops surface**. Plan defers standalone worker, but then ops must call the method somehow; not wired. Service unit tests cover happy fail→retry if invoked manually. | `outbox_notification_requested_handler`; `dispatch_delivery`; `process_due_failed`; `OutboxService.dispatch_claimed` | Document MVP contract explicitly: “outbox publishes once; delivery retry is `process_due_failed` job.” Wire a minimal in-process/test harness entry or ops note. Optionally raise from handler when status ∉ {SENT, CANCELLED, DEAD} if outbox-driven retry is preferred. |
| R-008 | **P2** | **Permission names diverge from plan matrix** without ADR. Plan: `notifications:templates:write`, `notifications:deliveries:read/write`, `reports:definitions:write`, `reports:runs:*`. Impl + YAML + seed: coarse `notifications:read/write/send`, `reports:read/write/run`. Consistent within code/YAML/migration seed — good — but plan still shows fine-grained names. | `permissions.yml`; `q0d1e2f3a4b5_…py` `NEW_PERMISSIONS` / `ROLE_GRANTS`; plan § permissions | Update plan to coarse set (recommended) or rename everything to plan names + reseed. |
| R-009 | **P2** | **HTTP always 201 on schedule/request**, including idempotent dedupe (`created=False`). Weak client signal for replay. | `endpoints/notifications.py` (`schedule_delivery`); `endpoints/reports.py` (`request_run`) | Return 200 when `created is False`, 201 when `True` (or always 200 with `created` flag). Test both. |
| R-010 | **P2** | **`execute_run` re-enters `FAILED` → `RUNNING`.** Terminal skip only for `SUCCEEDED` and `CANCELLED`. Outbox redelivery after a future real failure would re-run (good) or thrash (if always failing). Acceptable for placeholder MVP; no max-attempt on report runs. | `ReportService.execute_run` | When real exporters land: define redrive policy; optionally cap attempts or require explicit redrive. |
| R-011 | **P2** | **Stuck `SENDING` not claimed by `process_due_failed`.** Claim filter is `status == FAILED` only. Crash after flush to `SENDING` is recovered if outbox still PROCESSING (lease reclaim re-runs handler). After outbox `PUBLISHED`, a stuck `SENDING` would need manual repair. | `process_due_failed`; `dispatch_delivery` | Treat stale `SENDING` (e.g. `updated_at` older than N) as reclaimable, or never flush `SENDING` until provider returns (harder). Document ops. |
| R-012 | **P2** | **Dual handlers / dead param.** `NotificationService.handle_notification_requested(_db, …)` ignores `_db` (uses `self.db`); module-level `outbox_notification_requested_handler` is the path used by tests. Risk of divergent payload parsing later. | `app/services/notification.py` | Single `_extract_delivery_id(event)` helper; delete or thin-wrap the unused instance method. |
| R-013 | **P2** | **No list endpoints** for deliveries/runs (get-by-id only). Plan illustrative surface includes list; MVP may omit but ops visibility is weak. | `endpoints/notifications.py`; `endpoints/reports.py` | Optional follow-up: `GET /deliveries`, `GET /runs` with `notifications:read` / `reports:read`. |
| R-014 | **P2** | **Latent authz fallback for role name `MEMBER`.** In `is_authorized`, non-`:self` path allows `role.name == MEMBER` + `resource_owner_id == user.id` even when `tenant_matches` is false. No profile HTTP routes use this yet; `profile:read` is non-`:self`. Future misuse could cross-tenant if owner id is passed without tenant check. | `AuthorizationService.is_authorized` | Prefer migrating `profile:*` to `profile:*:self` + `require_self`, or require tenant_match for all non-platform grants. |
| R-015 | **P2** | **Stale bytecode only:** `endpoints/outbox.cpython-*.pyc` remains while `outbox.py` is gone. Harmless if source deleted and router not imported; clean for clarity. | `app/api/v1/endpoints/__pycache__/outbox.*` | Delete pyc in branch hygiene; ensure no import of missing module. |

---

## Prior Phase 16 review delta (`phase16_review_findings.md`)

| Prior ID | Status on this branch |
|----------|------------------------|
| P16-001 invalid `report.run.requested.v1` vs pattern | **Resolved** — pattern is multi-segment; `validate_event_type` accepts registered constant; R-005 **CLOSED** (docs aligned to multi-segment). |
| P16-002 missing permissions seed | **Resolved** — seed embedded in `q0d1e2f3a4b5` (`NEW_PERMISSIONS` + `ROLE_GRANTS` aligned with YAML roles). |
| P16-003 / no_provider never DEAD | **Mostly resolved** — `dispatch_delivery` promotes `no_provider` and soft-fail to `DEAD` at max attempts; retry still unscheduled (R-007). |
| P16-005 incomplete tests | **Partially improved** — service: dedupe, outbox path, fail→DEAD, `process_due_failed`; still missing API/RLS/architecture (R-001/002/006). |
| P16-006 `test_operational_mvp` schema | **Resolved** — creates templates/definitions with `code=`. |
| P16-010 UniqueConstraint vs partial unique | **Resolved** — models use `Index(..., unique=True, postgresql_where=...)`. |

---

## Dimension checklist

| Dimension | 15.5 | 16 | Notes |
|-----------|------|----|-------|
| Security: no public outbox inject | **OK** | **OK** | No outbox router; 404 tests; api.py comment. |
| Security: MEMBER BOLA / `*:self` | **OK** | N/A | `/me` + issue-self + require_self tests. |
| Security: staff send abuse | N/A | **GAP** | R-004 free-form recipient. |
| RBAC YAML | **OK** | **OK** | MEMBER lacks notif/report; GYM_* lack outbox. |
| RBAC DB seed | **OK** | **OK** | 15.5C + q0 seed; parity script name-based. |
| RBAC API tests | **OK** (entitlements) | **GAP** | R-001. |
| Event registry | **OK** | **OK** | Multi-segment `report.run.requested.v1`; R-005 **CLOSED** (docs-aligned). |
| Outbox max-attempts / fencing | **OK** | inherits | claim DEAD + lease CAS. |
| Reliability: delivery retry | N/A | **WEAK** | R-007 / R-011. |
| Tenancy filters | N/A | **OK** service | RLS tests missing R-002. |
| Schema / migration expand | N/A | **OK** | expand-only + code backfill + seed. |
| Domain boundary Membership→adapter | N/A | **OK** code | Fitness test missing R-006. |
| Tests for CI gate 16E | N/A | **PARTIAL** | Service strong; API/RLS weak. |

---

## What is good (do not regress)

### Phase 15.5C/D
1. **Generic outbox HTTP removed** — `api_router` has no outbox include; `test_public_outbox_routes_absent` asserts 404.
2. **`AuthorizationService.require_self` / `require_tenant`** — `*:self` cannot be used as tenant-wide grant; owner required.
3. **`/me/entitlements/check`** — resolves member via `MemberService.get_member_by_user_id`; never accepts client `member_id`.
4. **`OutboxService.claim_pending`** — filters `attempt_count < max_attempts`; stale exhausted PROCESSING → `DEAD` with `max_attempts_exceeded_on_claim`.
5. **`validate_event_type`** — pattern + `REGISTERED_EVENT_TYPES` allowlist on enqueue.
6. Hostile tests: fencing, max-attempts, BOLA, least-privilege YAML.

### Phase 16
1. Flow: `schedule_delivery` → same-TX `OutboxService.enqueue(NOTIFICATION_REQUESTED_V1)` → handler → `dispatch_delivery` → `LogNotificationProvider` (no network SDK).
2. Reports: `request_run` → `REPORT_RUN_REQUESTED_V1` → `execute_run` placeholder `memory://` export metadata.
3. **Adapters isolated** in `notification_providers.py`; default map EMAIL/SMS/WHATSAPP/PUSH → log.
4. **Dedupe** IntegrityError re-read pattern for deliveries and runs; partial unique indexes in models + migration.
5. **Composite FKs** template/definition with tenant; expand migration `q0d1e2f3a4b5` + RBAC seed matching YAML grants.
6. Service tests: render, dedupe, outbox publish path, fail→DEAD, process_due retry→SENT, report outbox→SUCCEEDED.
7. MEMBER has **no** notifications/reports grants in YAML (staff-only).

---

## Minimal unblock list (Phase 16 → READY_FOR_CI)

1. **R-001** API RBAC tests (MEMBER 403 + staff happy path sample).  
2. **R-002** Cross-tenant isolation tests for templates/deliveries/definitions/runs.  
3. **R-003** Remove client `enqueue_outbox` from HTTP schemas.  
4. **R-004** Tighten recipient binding on schedule (or role-restrict free-form).  
5. ~~**R-005** Align plan string ↔ `REPORT_RUN_REQUESTED_V1`~~ **CLOSED** (docs → `report.run.requested.v1`).  
6. **R-006** Architecture import test Membership ↛ providers.  
7. **R-007** Document or wire delivery retry job expectation.  

Then re-review; process-merge only after **Phase 15.5 LOCKED** on `main`.

---

## Verdict rationale

**Phase 15.5** implementation of trust boundaries is **code-ready** and already described as PR CI green; remaining gate is **human APPROVE + merge + main CI**, not further code defects found in this pass.

**Phase 16** is **past the earlier BLOCKED state** (invalid event type / missing seed fixed) but is **NEEDS_WORK** for merge readiness: incomplete 16E test surface, public schedule footguns, and contract/docs drift. No single remaining defect makes every path unrunnable, so not `BLOCKED` on code; not `READY_FOR_CI` until P1s above are closed.
)
