# Phase 16 Independent Review Findings

**Branch:** `feat/phase16-notifications-reports`  
**Reviewer role:** Independent code review (read-only)  
**Scope:** Notification/report models, services, providers, endpoints, migration, event registry, permissions, tests  
**Date:** 2026-08-10  

## Overall verdict: **NEEDS_WORK** (P1 harden path CLOSED 2026-08-10)

P0 event pattern + permission seed and the ordered P1 harden items are **CLOSED** on this branch:

- **P16-008:** no client `enqueue_outbox` on HTTP (always enqueue)
- **P16-003:** outbox handler raises `notification_delivery_not_sent` on non-SENT
- **P16-007:** `recipient_not_in_tenant` when `recipient_user_id` lacks tenant `UserRole`

Remaining: formal CI green, Phase 15.5 merge order (**15.5 still not LOCKED**), residual P2s / optional deep RLS, domain bridges deferred. Phase 16 is **not LOCKED** and **not production-ready**.

This review does **not** approve Phase 15.5 merge; it only assesses Phase 16 WIP.

---

## Closure log (2026-08-10 harden)

| ID | Status | Fix summary |
|----|--------|-------------|
| P16-001 | **CLOSED** | Pattern allows multi-segment actions; `report.run.requested.v1` registered and validated |
| P16-002 | **CLOSED** | Seed embedded in `q0d1e2f3a4b5_phase16_notifications_reports.py` + YAML parity |
| P16-003 | **CLOSED** | Outbox handler raises `notification_delivery_not_sent` when status ≠ SENT → outbox `mark_failed` retry; `process_due_failed` + fail→DEAD tested (`tests/services/test_notification.py`) |
| P16-004 | **CLOSED** | `no_provider` uses same max-attempt → DEAD branch |
| P16-005 | **PARTIAL→CLOSED (MVP)** | fail→DEAD, `process_due_failed`, outbox fail→FAILED, MEMBER 403 API tests present; full RLS isolation suite still optional follow-up |
| P16-006 | **CLOSED** | `test_operational_mvp.py` supplies required `code=` for templates/definitions |
| P16-007 | **CLOSED (MVP)** | `recipient_user_id` → `UserRole` tenant bind raises `recipient_not_in_tenant`; free-form address still staff-allowed (non-empty + max-length) |
| P16-008 | **CLOSED** | No client `enqueue_outbox` on HTTP; schemas omit field; endpoints always `enqueue_outbox=True` (service-internal for tests) |
| P16-009 | **CLOSED (doc)** | Plan documents coarse `notifications:read/write/send` + `reports:read/write/run` matching YAML/seed |

---

## Findings

| ID | Severity | Finding | File | Recommendation |
|----|----------|---------|------|----------------|
| P16-001 | **P0** **CLOSED** | `REPORT_RUN_REQUESTED_V1 = "report.run.requested.v1"` **fails** `EVENT_TYPE_PATTERN` (`domain.action.vN` — exactly two dotted segments before `vN`). `OutboxService.enqueue` → `validate_event_type` will raise `EventTypeValidationError` for every `ReportService.request_run(..., enqueue_outbox=True)`. Phase plan explicitly specifies `report.run_requested.v1`. Implementation is wrong vs both the regex and `phase16_notifications_reports.md`. | `app/core/event_types.py` (`REPORT_RUN_REQUESTED_V1`); consumers: `app/services/report.py` (`request_run`, `outbox_report_run_requested_handler`); tests hardcode the bad string in `tests/services/test_report.py` | **CLOSED:** `EVENT_TYPE_PATTERN` allows multi-segment actions; type registered. |
| P16-002 | **P0** **CLOSED** | **Permissions YAML updated but no Alembic seed migration** for `notifications:read/write/send` and `reports:read/write/run` (or role grants). Prior phases always ship `seed_*_permissions.py`. `scripts/check_permissions_db.py` will fail YAML↔DB parity after `alembic upgrade head` (permissions in YAML missing from DB; role grants empty). Runtime RBAC on real DB = **403 for all staff** even when YAML looks correct. | `permissions.yml`; missing `alembic/versions/*_seed_notification_report_permissions.py` (compare `m6f7a8b9c0d1_seed_outbox_permissions.py`) | **CLOSED:** seed in `q0d1e2f3a4b5` + role grants. |
| P16-003 | **P1** **CLOSED** | **Provider failure does not keep outbox retry alive.** `outbox_notification_requested_handler` / `dispatch_delivery` return success even when delivery ends `FAILED`/`DEAD`. `OutboxService.dispatch_claimed` then `mark_published`. Retry of failed **deliveries** depends solely on `NotificationService.process_due_failed`, which has **no worker, cron, or HTTP surface** and is untested. After first provider failure, delivery sits in `FAILED` until an unscheduled method is called. | `app/services/notification.py` (`dispatch_delivery`, `outbox_notification_requested_handler`, `process_due_failed`) | **CLOSED:** handler raises on non-SENT; outbox mark_failed; tests cover raise + process_due. |
| P16-004 | **P1** **CLOSED** | **`no_provider` path never promotes to `DEAD`.** In `dispatch_delivery`, if `self.providers.get(delivery.channel) is None`, status is always set to `DELIVERY_FAILED` and return — **no** `attempt_count >= max_attempts → DEAD` branch. `process_due_failed` filters `attempt_count < max_attempts`, so after N attempts the row is stuck `FAILED` forever (not `DEAD`), invisible to both outbox and due processor. | `app/services/notification.py` (`dispatch_delivery`) | **CLOSED:** max-attempt → DEAD on no_provider. |
| P16-005 | **P1** **CLOSED (MVP)** | **16E required tests missing / incomplete.** Plan requires: Fail provider → FAILED → `process_due_failed` → DEAD; API/RBAC; RLS cross-tenant isolation for templates/deliveries/definitions/runs; architecture (Membership must not import providers); event registry for report type. Present: happy-path service tests only (`test_notification.py`, `test_report.py`). **No** `FailingNotificationProvider` usage, **no** API tests under `tests/api/`, **no** report API tests, **no** process_due/DEAD coverage. | `tests/services/test_notification.py`; `tests/services/test_report.py`; missing `tests/api/test_notifications.py`, `tests/api/test_reports.py` | **CLOSED (MVP):** fail→DEAD, process_due, outbox fail, MEMBER 403 API (`test_notifications_reports_rbac.py`). Full RLS isolation still optional. |
| P16-006 | **P1** **CLOSED** | **`test_operational_mvp.py` was schema-stale** (missing `code=`). | `tests/test_operational_mvp.py` | **CLOSED:** creates templates/definitions with required `code=`. |
| P16-007 | **P1** **CLOSED (MVP)** | **Staff can schedule to arbitrary `recipient_address` / any `recipient_user_id` with no membership/tenant binding proof.** `schedule_delivery` only checks “address or user id present”. `recipient_user_id` FK is to global `users.id` (not composite tenant). `POST /notifications/deliveries` with `notifications:send` (granted to FRONT_DESK) is an abuse / spam / horizontal spoof vector (notify any email/phone; attach any user UUID). Not classic member BOLA via `/me`, but production-grade authz gap for a send API. | `app/services/notification.py` (`schedule_delivery`); `app/api/v1/endpoints/notifications.py` (`schedule_delivery`); `app/models/notification.py` (`recipient_user_id`) | **CLOSED (MVP):** UserRole.tenant_id bind for `recipient_user_id`; address non-empty + max length; free-form still staff-allowed by design. |
| P16-008 | **P1** **CLOSED** | **Client-controlled `enqueue_outbox` on public HTTP.** `DeliveryScheduleRequest.enqueue_outbox` and `RunRequest.enqueue_outbox` default True but are client-settable. Client can force `False` → `PENDING` delivery/run with **no** outbox row and no dispatch path (unless internal code calls `dispatch_delivery`/`execute_run`). Footgun + potential “silent no-op” for ops. | `endpoints/notifications.py`, `endpoints/reports.py` | **CLOSED:** field removed from HTTP schemas; always `enqueue_outbox=True`. |
| P16-009 | **P1** **CLOSED (doc)** | Permission names were sketched fine-grained in plan vs coarse impl. | `permissions.yml`; endpoints; plan | **CLOSED (doc):** plan now documents coarse `notifications:read/write/send` + `reports:read/write/run` as source of truth with YAML/seed. |
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
| Security: no public outbox inject | **OK** | No outbox router; api comment + 15.5C preserved; HTTP never exposes client `enqueue_outbox` (P16-008 **CLOSED**) |
| RBAC separation | **OK (seed)** | Endpoint `_require` + coarse perms; seed in `q0d1e2f3a4b5`; MEMBER ungranted in YAML; plan name drift remains P16-009 |
| BOLA / horizontal | **OK (MVP)** | Tenant-scoped get_*; `recipient_user_id` tenant-bound (`recipient_not_in_tenant`); free-form address still staff MVP |
| Idempotency / dedupe_key | **OK (service)** | IntegrityError re-read pattern mirrors outbox; unique constraints intended |
| Outbox `event_type` registered | **OK** | `notification.requested.v1` + multi-segment `report.run.requested.v1` registered (P16-001 **CLOSED**) |
| Crash/retry deliveries | **OK (MVP)** | Handler raises `notification_delivery_not_sent` on non-SENT; no_provider → DEAD at max; process_due tested; standalone worker deferred |
| Domain boundary (no Membership→WhatsApp) | **OK** | Membership does not call NotificationService/providers; adapters isolated |
| Schema drift model vs migration | **PARTIAL** | Expand migration `q0d1e2f3a4b5` covers columns; partial unique vs model drift may remain (P16-010) |
| Missing tests / API / permissions seed | **MVP OK** | Service + API/RBAC present; seed present; full RLS isolation optional |
| Race / FOR UPDATE | **MOSTLY OK** | `dispatch_delivery` + `execute_run` lock; `process_due_failed` uses `skip_locked` |
| Code quality / mypy hazards | **P2 residual** | Dual handlers, 201-on-dedupe; client `enqueue_outbox` **CLOSED** |

---

## What is good (do not regress)

1. **Correct high-level flow for notifications:** `schedule_delivery` → same-TX `OutboxService.enqueue(NOTIFICATION_REQUESTED_V1)` → handler → `dispatch_delivery` → `LogNotificationProvider` (no network SDKs).
2. **`notification.requested.v1` / `report.run.requested.v1` registered** under multi-segment `EVENT_TYPE_PATTERN`.
3. **Providers are adapter-only** (`notification_providers.py`); domain does not import WhatsApp/Email SDKs.
4. **No reintroduction of public `/outbox` HTTP inject**; HTTP always enqueues outbox (no client flag).
5. **Expand-only migration** `q0d1e2f3a4b5_phase16_notifications_reports.py` with backfill for `code` + permissions seed.
6. **Service-layer tenant filters + FOR UPDATE** on dispatch/execute; outbox handler raises `notification_delivery_not_sent` on non-SENT.
7. **YAML does not grant notification/report perms to MEMBER**; keeps outbox/inbox off GYM_* roles (15.5C).
8. **`recipient_user_id` tenant-bound** via `UserRole` (`recipient_not_in_tenant`).

---

## Minimal unblock list (ordered)

1. ~~Fix `REPORT_RUN_REQUESTED_V1` / pattern (P16-001)~~ **CLOSED**
2. ~~Permissions seed (P16-002)~~ **CLOSED**
3. ~~Delivery retry raise + DEAD / process_due (P16-003, P16-004)~~ **CLOSED**
4. ~~16E MVP tests: DEAD, process_due, MEMBER 403 (P16-005)~~ **CLOSED (MVP)**; optional full RLS isolation suite
5. ~~HTTP always enqueue; recipient tenant bind (P16-007, P16-008)~~ **CLOSED**
6. ~~`test_operational_mvp` schema (P16-006)~~ **CLOSED**
7. Formal gates: PR CI green; Phase 15.5 merge-first; do not self-merge Phase 16
8. Residual hygiene: P2s (201-on-dedupe, execute_run terminals, architecture fitness); optional deep RLS suite

---

## Verdict rationale

**NEEDS_WORK** (was BLOCKED): P0 event/seed and harden P1s (**including no client `enqueue_outbox`, outbox `notification_delivery_not_sent` raise, `recipient_not_in_tenant`**) are **CLOSED** on branch. Phase 16 is **not LOCKED** and **not production-ready**.

Remaining before READY / merge:

- Formal PR CI (Security / Lint / Unit+Integration) green on branch
- Phase 15.5 **LOCKED on `main` first** (stack base) — 15.5 is still **not LOCKED**
- Residual: P2s, optional deep RLS / architecture fitness, domain→notification bridges deferred

Do not merge Phase 16 ahead of Phase 15.5 LOCKED on `main` (plan merge order).
