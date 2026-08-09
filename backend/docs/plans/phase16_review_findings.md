# Phase 16 Independent Review Findings

**Branch:** `feat/phase16-notifications-reports`  
**Reviewer role:** Independent code review (read-only)  
**Scope:** Notification/report models, services, providers, endpoints, migration, event registry, permissions, tests  
**Date:** 2026-08-10  

## Overall verdict: **BLOCKED**

Do **not** merge or call Phase 16 ready. Core report outbox contract is invalid against the versioned event-type pattern, permissions are not seeded into DB, retry/DEAD and several 16E gates are incomplete, and CI would fail on event-type + permissions parity checks.

This review does **not** approve Phase 15.5 merge; it only assesses Phase 16 WIP.

---

## Findings

| ID | Severity | Finding | File | Recommendation |
|----|----------|---------|------|----------------|
| P16-001 | **P0** | `REPORT_RUN_REQUESTED_V1 = "report.run.requested.v1"` **fails** `EVENT_TYPE_PATTERN` (`domain.action.vN` — exactly two dotted segments before `vN`). `OutboxService.enqueue` → `validate_event_type` will raise `EventTypeValidationError` for every `ReportService.request_run(..., enqueue_outbox=True)`. Phase plan explicitly specifies `report.run_requested.v1`. Implementation is wrong vs both the regex and `phase16_notifications_reports.md`. | `app/core/event_types.py` (`REPORT_RUN_REQUESTED_V1`); consumers: `app/services/report.py` (`request_run`, `outbox_report_run_requested_handler`); tests hardcode the bad string in `tests/services/test_report.py` | Rename constant to **`report.run_requested.v1`** (or extend pattern + document ADR if multi-segment types are desired — do not leave a registered type that `validate_event_type` rejects). Update registry, service, and all tests. Run `test_registered_event_types_allowed` and report outbox tests; they currently assert a type that must fail pattern validation. |
| P16-002 | **P0** | **Permissions YAML updated but no Alembic seed migration** for `notifications:read/write/send` and `reports:read/write/run` (or role grants). Prior phases always ship `seed_*_permissions.py`. `scripts/check_permissions_db.py` will fail YAML↔DB parity after `alembic upgrade head` (permissions in YAML missing from DB; role grants empty). Runtime RBAC on real DB = **403 for all staff** even when YAML looks correct. | `permissions.yml`; missing `alembic/versions/*_seed_notification_report_permissions.py` (compare `m6f7a8b9c0d1_seed_outbox_permissions.py`) | Add seed revision after `q0d1e2f3a4b5`: insert permission rows + `role_permissions` for GYM_OWNER/ADMIN/MANAGER/FRONT_DESK/ACCOUNTANT matching YAML. Ensure CI runs `check_permissions_db` green. |
| P16-003 | **P1** | **Provider failure does not keep outbox retry alive.** `outbox_notification_requested_handler` / `dispatch_delivery` return success even when delivery ends `FAILED`/`DEAD`. `OutboxService.dispatch_claimed` then `mark_published`. Retry of failed **deliveries** depends solely on `NotificationService.process_due_failed`, which has **no worker, cron, or HTTP surface** and is untested. After first provider failure, delivery sits in `FAILED` until an unscheduled method is called. | `app/services/notification.py` (`dispatch_delivery`, `outbox_notification_requested_handler`, `process_due_failed`) | Either: (a) raise from handler when status is not `SENT` so outbox `mark_failed` + `available_at` backoff reclaims, **or** (b) wire a worker loop that calls `process_due_failed` (and document it as the only retry path) + tests for FAIL→retry→DEAD. Prefer (a) for consistency with outbox lease/max-attempt machinery already proven in Phase 15. |
| P16-004 | **P1** | **`no_provider` path never promotes to `DEAD`.** In `dispatch_delivery`, if `self.providers.get(delivery.channel) is None`, status is always set to `DELIVERY_FAILED` and return — **no** `attempt_count >= max_attempts → DEAD` branch. `process_due_failed` filters `attempt_count < max_attempts`, so after N attempts the row is stuck `FAILED` forever (not `DEAD`), invisible to both outbox and due processor. | `app/services/notification.py` (`dispatch_delivery`) | Apply the same max-attempt → `DEAD` logic used on provider soft-fail; add unit test with missing provider mapping. |
| P16-005 | **P1** | **16E required tests missing / incomplete.** Plan requires: Fail provider → FAILED → `process_due_failed` → DEAD; API/RBAC; RLS cross-tenant isolation for templates/deliveries/definitions/runs; architecture (Membership must not import providers); event registry for report type. Present: happy-path service tests only (`test_notification.py`, `test_report.py`). **No** `FailingNotificationProvider` usage, **no** API tests under `tests/api/`, **no** report API tests, **no** process_due/DEAD coverage. | `tests/services/test_notification.py`; `tests/services/test_report.py`; missing `tests/api/test_notifications.py`, `tests/api/test_reports.py` | Implement plan table 16E before claiming CI-ready. At minimum: fail/retry/DEAD, cross-tenant query isolation, MEMBER 403 on `/notifications/*` and `/reports/*`, registry acceptance of fixed report type. |
| P16-006 | **P1** | **`test_operational_mvp.py` is schema-stale.** Creates `ReportDefinition(..., name=..., config=...)` and `NotificationTemplate(..., name=..., channel=..., body_template=...)` without required `code` (and related NOT NULL columns). Will fail insert/flush against current models / migrated schema. | `tests/test_operational_mvp.py` | Pass `code=` (and any other required fields) or rewrite to use services. |
| P16-007 | **P1** | **Staff can schedule to arbitrary `recipient_address` / any `recipient_user_id` with no membership/tenant binding proof.** `schedule_delivery` only checks “address or user id present”. `recipient_user_id` FK is to global `users.id` (not composite tenant). `POST /notifications/deliveries` with `notifications:send` (granted to FRONT_DESK) is an abuse / spam / horizontal spoof vector (notify any email/phone; attach any user UUID). Not classic member BOLA via `/me`, but production-grade authz gap for a send API. | `app/services/notification.py` (`schedule_delivery`); `app/api/v1/endpoints/notifications.py` (`schedule_delivery`); `app/models/notification.py` (`recipient_user_id`) | Validate recipient: member/user bound to tenant (or staff-only allowlist). Prefer resolving address from tenant-owned Member/UserDevice, not free-form from client for production paths. Restrict free-form schedule to higher roles or internal services only. |
| P16-008 | **P1** | **Client-controlled `enqueue_outbox` on public HTTP.** `DeliveryScheduleRequest.enqueue_outbox` and `RunRequest.enqueue_outbox` default True but are client-settable. Client can force `False` → `PENDING` delivery/run with **no** outbox row and no dispatch path (unless internal code calls `dispatch_delivery`/`execute_run`). Footgun + potential “silent no-op” for ops. | `endpoints/notifications.py`, `endpoints/reports.py` | Do not accept `enqueue_outbox` from clients; always enqueue on schedule/request. Keep flag service-internal for tests only. |
| P16-009 | **P1** | **Permission names diverge from plan contract** without ADR. Plan: `notifications:templates:write`, `notifications:deliveries:read/write`, `reports:definitions:write`, `reports:runs:write/read`. Impl: coarse `notifications:read/write/send`, `reports:read/write/run`. Acceptable if intentional, but seed, YAML, and API must stay consistent and documented; current plan vs code drift risks wrong seed work. | `permissions.yml`; `endpoints/notifications.py`; `endpoints/reports.py`; `docs/plans/phase16_notifications_reports.md` | Either align names to plan or update plan + stick to coarse set everywhere (recommend one source of truth). |
| P16-010 | **P2** | **Model `UniqueConstraint(tenant_id, dedupe_key)` vs migration partial unique index** (`WHERE dedupe_key IS NOT NULL`) named the same (`uq_notification_deliveries_tenant_dedupe` / `uq_report_runs_tenant_dedupe`). Migration uses `create_index(..., unique=True, postgresql_where=...)`; model uses non-partial `UniqueConstraint`. Alembic autogenerate / metadata parity drift; SQLite `create_all` paths differ from PG. Functionally multi-NULL is OK on both PG unique forms, but names/types differ. | `app/models/notification.py`, `app/models/report.py`; `alembic/versions/q0d1e2f3a4b5_phase16_notifications_reports.py` | Prefer partial unique indexes in model via `Index(..., unique=True, postgresql_where=...)` matching migration, or document intentional PG-only partial indexes and keep `alembic check` clean. |
| P16-011 | **P2** | **`execute_run` terminal-state holes.** Early-return only for `REPORT_STATUS_SUCCEEDED`. `CANCELLED` (and optionally intentional terminal `FAILED`) can be resurrected to `RUNNING` on outbox redelivery. No `skip_locked` (blocks concurrent workers — acceptable MVP, but note). | `app/services/report.py` (`execute_run`) | Treat `CANCELLED` (and maybe terminal `FAILED` without redrive policy) as no-op returns; consider `with_for_update(skip_locked=True)` if multi-worker. |
| P16-012 | **P2** | **Duplicate / inconsistent outbox payload handlers.** `NotificationService.handle_notification_requested` uses `is_envelope_data` + careful nesting; module-level `outbox_notification_requested_handler` only does `payload.get("data", payload)` and ignores envelope validation. Dead `_db` param on instance method (always uses `self.db`). Risk of double-nesting / wrong parse if envelope shape evolves. | `app/services/notification.py` | Single shared `_extract_delivery_id(event)` used by both; delete unused path or wire one. |
| P16-013 | **P2** | **Index / worker design: `process_due_failed` is tenant-scoped only; claim index `ix_notification_deliveries_available` is `(status, available_at)` without `tenant_id`.** Fine for per-tenant jobs; multi-tenant worker must loop tenants or add a global claim API with composite index `(status, available_at, tenant_id)`. | `app/models/notification.py`; `NotificationService.process_due_failed` | Document worker topology; if platform worker processes all tenants, add method + index including `tenant_id`. |
| P16-014 | **P2** | **HTTP 201 on idempotent dedupe hit** for deliveries/runs (`created=False` still returns status_code=201). Weak REST/idempotency signal. | `endpoints/notifications.py` (`schedule_delivery`); `endpoints/reports.py` (`request_run`) | Return 200 when `created is False`, 201 when True (or always 200 with `created` flag — pick one and test). |
| P16-015 | **P2** | **`test_operational` / package hygiene:** `app/api/v1/endpoints/__init__.py` is empty (OK if submodule imports). Unused import `and_` in `notification.py`. `test_report.py` defines local `REPORT_RUN_REQUESTED_V1` instead of importing from `event_types` (comment admits registry lag — now stale and wrong). | `notification.py`; `tests/services/test_report.py` | Import canonical constant; remove dead import. |
| P16-016 | **P2** | **Plan exit criteria unchecked:** domain→event bridges (e.g. membership.activated → schedule) not present — OK as deferred only if documented; ensure Membership still never imports `notification_providers` (currently true — keep a regression test). | `app/services/membership.py` (clean); missing architecture test | Add lightweight import/architecture test forbidding membership→providers. |

---

## Dimension checklist (summary)

| Dimension | Status | Notes |
|-----------|--------|-------|
| Tenancy: `tenant_id` on queries | **OK** | Service queries filter `tenant_id`; composite FKs to template/definition present |
| Composite FKs | **OK** | `fk_notification_deliveries_template_tenant`, `fk_report_runs_definition_tenant` |
| Security: no public outbox inject | **OK** | No outbox router; api comment + 15.5C preserved |
| RBAC separation | **PARTIAL** | Endpoint `_require` + distinct perms; **DB seed missing (P0)**; MEMBER correctly unganted in YAML |
| BOLA / horizontal | **PARTIAL** | Tenant-scoped get_delivery/get_run OK; free-form recipient send is abuse risk (P16-007) |
| Idempotency / dedupe_key | **OK (service)** | IntegrityError re-read pattern mirrors outbox; unique constraints intended |
| Outbox `event_type` registered | **BLOCKED** | `notification.requested.v1` OK; **`report.run.requested.v1` invalid pattern (P16-001)** |
| Crash/retry deliveries | **WEAK** | FOR UPDATE good; FAILED path not wired to durable worker; no_provider never DEAD |
| Domain boundary (no Membership→WhatsApp) | **OK** | Membership does not call NotificationService/providers; adapters isolated |
| Schema drift model vs migration | **PARTIAL** | Expand migration `q0d1e2f3a4b5` largely covers columns; partial unique vs UniqueConstraint drift (P16-010) |
| Missing tests / API / permissions seed | **BLOCKED** | APIs exist; seed missing; 16E gaps; report event type will break tests |
| Race / FOR UPDATE | **MOSTLY OK** | `dispatch_delivery` + `execute_run` lock; `process_due_failed` uses `skip_locked` |
| Code quality / mypy hazards | **P2** | Dead `_db`, dual handlers, client `enqueue_outbox`, 201-on-dedupe |

---

## What is good (do not regress)

1. **Correct high-level flow for notifications:** `schedule_delivery` → same-TX `OutboxService.enqueue(NOTIFICATION_REQUESTED_V1)` → handler → `dispatch_delivery` → `LogNotificationProvider` (no network SDKs).
2. **`notification.requested.v1` is valid `domain.action.vN` and registered.**
3. **Providers are adapter-only** (`notification_providers.py`); domain does not import WhatsApp/Email SDKs.
4. **No reintroduction of public `/outbox` HTTP inject.**
5. **Expand-only migration** `q0d1e2f3a4b5_phase16_notifications_reports.py` with backfill for `code` is the right schema strategy.
6. **Service-layer tenant filters + FOR UPDATE** on dispatch/execute.
7. **YAML does not grant notification/report perms to MEMBER**; keeps outbox/inbox off GYM_* roles (15.5C).

---

## Minimal unblock list (ordered)

1. Fix `REPORT_RUN_REQUESTED_V1` → `report.run_requested.v1` (P16-001); green `tests/core/test_event_types.py` + report outbox tests.
2. Add permissions seed migration aligned with `permissions.yml` (P16-002); green `check_permissions_db`.
3. Close delivery retry loop (raise on non-SENT **or** wire + test `process_due_failed`) and DEAD for `no_provider` (P16-003, P16-004).
4. Fill 16E tests: DEAD path, API RBAC, tenancy isolation, fix `test_operational_mvp` (P16-005, P16-006).
5. Harden schedule API: server-side outbox always on; recipient binding (P16-007, P16-008).

---

## Verdict rationale

**BLOCKED** because:

- Report async path is **contract-broken at enqueue** (invalid event type string).
- RBAC matrix in YAML has **no DB seed**, so permissions parity gate and real authz fail.
- Crash/retry semantics for deliveries are **incomplete** relative to Phase 15 outbox guarantees and the Phase 16 plan.
- Required test surface (16E) is **not met**.

After P0s and P1 retry/seed/tests are fixed, re-review for **NEEDS_WORK → READY**. Do not merge Phase 16 ahead of Phase 15.5 LOCKED on `main` (plan merge order).
