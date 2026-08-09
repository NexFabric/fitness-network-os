# Phase 16 — Notifications & Reports API

**Status:** 🟠 IN PROGRESS on `feat/phase16-notifications-reports`  
**Depends on:** Phase 15.5 integrity closure **LOCKED on main** (merge order: **15.5 first, then 16**)  
**Stacked on:** Phase 15.5 branch work (outbox fencing, event registry, no public generic inbox)  
**Plan path:** `backend/docs/plans/phase16_notifications_reports.md`  
**Do not claim:** production-ready (Phase 26 exit gate only)

## Goal

Ship tenant-scoped **notification scheduling/delivery** and **report definition/run** services + API that respect domain boundaries and the transactional outbox spine:

```text
Domain write (same TX)
  → schedule / request (flush-only service)
  → OutboxService.enqueue (canonical event_type)
  → worker claim SKIP LOCKED
  → Notification / Report consumer
  → Adapter (log provider MVP) or report executor
  → delivery/run status update
```

**Hard rules (AGENTS / MASTER_SPEC):**

- Gym = tenant; User ≠ Member; all tenant tables: `tenant_id` + index + RLS + tenancy tests.
- **No** Membership → WhatsApp (or any transport) shortcut.  
  Correct path: **Domain → Event → Outbox → Notification consumer → Adapter**.
- **No generic public `/inbox`** (or `/outbox/events`) reintroduction.  
  Provider webhooks land **later** (post-16 or later slice): signature → tenant from integration config → allowlist/normalize → `receive_inbox` → fast ACK → worker.
- Services **flush-only**; API commits; money still `amount_minor` (reports must not reintroduce floats for financial aggregates).
- Outbox enqueue only for **registered** `domain.action.vN` event types.

---

## Prerequisites (merge gate)

| Gate | Requirement |
|------|-------------|
| Phase 15.5 | Independent APPROVE → merge to `main` → main CI green → docs **LOCKED** |
| Then Phase 16 | Merge/rebase `feat/phase16-notifications-reports` onto main with 15.5 locked base |
| CI | Unit/Integration + Security + Lint + tenancy gates green before Phase 17 |

Phase 16 implementation may proceed on a stacked feature branch, but **must not** be treated as main-locked until 15.5 is locked and 16 PR is merged with green CI.

---

## Wave map

| Wave | Name | Outcome |
|------|------|---------|
| **16A** | Contracts / models | Templates, deliveries, report definitions/runs expanded; event types registered; permissions seed |
| **16B** | Service schedule + outbox | `NotificationService.schedule_delivery` + outbox enqueue; consumer dispatches delivery |
| **16C** | Adapters (log provider) | Provider protocol + `LogNotificationProvider` only (no real WhatsApp/SMS/Email SDK) |
| **16D** | Reports | Definitions + async runs via outbox; MVP executor (metadata / placeholder export) |
| **16E** | Tests / CI | Real PG service + API tests; RBAC; RLS; dedupe; retry/DEAD; CI green |

---

## 16A — Contracts / models

### Existing foundation (Wave 5 MODEL)

Tables already exist from operational MVP + composite FK work:

- `notification_templates`, `notification_deliveries` (RLS)
- `report_definitions`, `report_runs` (RLS)

Phase 16 **promotes** MODEL → service/API and expands columns as needed (expand-only migrations; no destructive CONTRACT unless a later revision).

### Notification model contracts

| Entity | Key fields / constraints |
|--------|---------------------------|
| `NotificationTemplate` | `tenant_id`, `code`, `name`, `channel`, subject/body templates, `is_active`, optional `locale`; **UNIQUE(tenant_id, code)** |
| `NotificationDelivery` | channel, recipient (user and/or address), status lifecycle, body/subject snapshot, `context` JSON, `attempt_count`, `available_at`, `dedupe_key`, provider ids, source event refs; **UNIQUE(tenant_id, dedupe_key)**; composite FK to template |

**Channels (string enum, expand-friendly):** `EMAIL`, `SMS`, `WHATSAPP`, `PUSH`.

**Delivery status lifecycle:**

```text
PENDING | QUEUED → SENDING → SENT
                 ↘ FAILED → (retry when available_at due) → SENT | DEAD
                 ↘ CANCELLED
```

### Report model contracts

| Entity | Key fields / constraints |
|--------|---------------------------|
| `ReportDefinition` | `code`, `name`, `report_type`, `config` JSON, `is_active`; **UNIQUE(tenant_id, code)** |
| `ReportRun` | `definition_id`, status, parameters, export_format, result_url, row_count, dedupe_key, timestamps; **UNIQUE(tenant_id, dedupe_key)**; composite FK to definition |

**Run status:** `PENDING` → `RUNNING` → `SUCCEEDED` | `FAILED` | `CANCELLED`.

MVP stores **export metadata** (`result_url`, `row_count`), not encrypted blobs (MASTER_SPEC report_exports / signed links deferred).

### Event type registry (outbox production path)

Register (and keep versioned) at least:

| Constant | Type string | Producer |
|----------|-------------|----------|
| `NOTIFICATION_REQUESTED_V1` | `notification.requested.v1` | Notification schedule |
| `NOTIFICATION_EMAIL_V1` | `notification.email.v1` | Optional narrow channel event (if used) |
| `REPORT_RUN_REQUESTED_V1` | `report.run_requested.v1` | Report run request |

Unknown well-formed types remain **DENY** on enqueue (15.5D invariant).

### Permissions (seed + YAML parity)

Introduce least-privilege grants (names illustrative; align with `permissions.yml` + DB seed):

| Permission | Typical roles | Surface |
|------------|---------------|---------|
| `notifications:templates:write` | GYM_OWNER / GYM_MANAGER | create/list templates |
| `notifications:deliveries:read` | GYM_OWNER / GYM_MANAGER | list/get deliveries |
| `notifications:deliveries:write` | GYM_OWNER / GYM_MANAGER (ops) | manual schedule (if exposed) |
| `reports:definitions:write` | GYM_OWNER / GYM_MANAGER | create/list definitions |
| `reports:runs:write` | GYM_OWNER / GYM_MANAGER | request run |
| `reports:runs:read` | GYM_OWNER / GYM_MANAGER | get run status |

MEMBER: **no** tenant-wide notification dump / report run of other members without `*:self` design (defer self-facing product until needed).  
GYM_* must **not** regain generic `outbox:*` / `inbox:*` write from 15.5C removal.

### Migration plan

- Expand-only Alembic revision(s) for missing columns/indexes/uniques if models diverge from applied schema.
- Permissions seed revision (or combined with expand if small).
- `alembic check` clean; never rewrite applied expand bodies.

---

## 16B — Service schedule + outbox

### NotificationService (flush-only)

| Operation | Behavior |
|-----------|----------|
| `create_template` / `get` / `list` | Tenant-scoped CRUD lite |
| `schedule_delivery` | Validate channel + recipient; optional template render (`string.Template` safe substitute); insert delivery; optional **same-TX** `OutboxService.enqueue(notification.requested.v1, {delivery_id, channel}, dedupe_key=notif-req:{id})` |
| `dispatch_delivery` | `FOR UPDATE` row; SENDING + attempt++; call provider; SENT or FAILED/DEAD |
| `process_due_failed` | Claim FAILED due rows (`SKIP LOCKED`); re-dispatch without re-injecting public inbox |
| Outbox handler | Resolve `delivery_id` from envelope `data`; call `dispatch_delivery` |

**Dedupe:** `UNIQUE(tenant_id, dedupe_key)` + IntegrityError → return existing (`created=False`).

**Retry:** exponential or fixed backoff via `available_at`; max attempts → `DEAD` (mirror outbox max-attempt spirit; no infinite crash loops).

### Outbox integration

```text
schedule_delivery(..., enqueue_outbox=True)
  → delivery status QUEUED
  → outbox row NOTIFICATION_REQUESTED_V1
  → worker / test harness claims + handler
  → dispatch_delivery → Log provider → SENT
```

Domain services that need notifications (membership activated, payment received, etc.) **enqueue domain events or call NotificationService in-process** — they must **not** import WhatsApp/Email SDKs.

### Explicit non-goals for ingress

- ❌ `POST /outbox/inbox` or generic tenant event dump API  
- ❌ Public “notification firehose” without authz  
- ✅ Later: **provider-specific** webhook routes only (signature verified, tenant from integration, normalize → inbox)

---

## 16C — Adapters (log provider)

### Protocol

```text
NotificationProvider
  name: str
  async send(delivery) → ProviderResult(success, provider, provider_message_id?, error?)
```

### MVP adapters

| Provider | Role |
|----------|------|
| `LogNotificationProvider` | Default for EMAIL/SMS/WHATSAPP/PUSH — always succeeds, no network I/O, synthetic `provider_message_id` |
| `FailingNotificationProvider` | Test-only forced failure |

`default_providers()` maps all allowed channels → log provider.

### Deferred transports

- Real WhatsApp / SMS / Email / Push SDKs  
- Provider webhook delivery receipts  
- Secret storage for provider credentials (Vault/KMS paths)  
- Per-tenant notification quota metering (MASTER_SPEC)

---

## 16D — Reports

### ReportService (flush-only)

| Operation | Behavior |
|-----------|----------|
| `create_definition` / `get_by_code` / `list` | Tenant-scoped definition catalog |
| `request_run` | Resolve active definition; create `ReportRun` PENDING; enqueue `report.run_requested.v1` with `{run_id, definition_code}`; dedupe via `dedupe_key` |
| `execute_run` | Transition RUNNING → SUCCEEDED with **placeholder** `result_url` (e.g. `memory://…`) and `row_count=0` MVP; or FAILED on error |
| Outbox handler | Load run_id → `execute_run` |

### API surface (illustrative)

- `POST /reports/definitions`, `GET /reports/definitions`  
- `POST /reports/runs` (definition_code + parameters + optional Idempotency-Key / dedupe_key)  
- `GET /reports/runs/{id}`  

### Deferred (MASTER_SPEC 156–157)

- `report_exports` blob store + encryption  
- Short-lived signed download links + auto-delete  
- `scheduled_reports` cron  
- Real SQL/metric executors and authorization snapshot for large exports  

---

## 16E — Tests / CI

### Required tests (real PostgreSQL where domain tests already use PG)

| Area | Cases |
|------|--------|
| Templates / schedule | Create template; schedule with render; invalid channel DENY |
| Dedupe | Same `dedupe_key` returns same delivery / run (`created=False`) |
| Outbox path | Schedule → enqueue registered type → handler → SENT via log provider |
| Retry / DEAD | Forced fail provider → FAILED → process_due → DEAD after max attempts |
| Reports | Definition + request_run → outbox → execute_run SUCCEEDED; duplicate dedupe |
| Event registry | Unregistered type cannot enqueue; `report.run_requested.v1` registered |
| RBAC | Permission matrix grants; MEMBER cannot list tenant deliveries if not granted |
| RLS / tenancy | Cross-tenant isolation on templates, deliveries, definitions, runs |
| Ingress safety | No generic public inbox/outbox inject routes reappear |
| Architecture | Domain boundary fitness: no Membership service import of notification providers |

### CI gates

- Lint / mypy (as enforced today)  
- Unit + Integration suite  
- Permissions YAML ↔ DB parity script  
- Tenancy schema linter  
- Security / CodeQL as required on PR  

### Exit criteria

- [ ] 16A–16D implemented behind routers + services  
- [ ] Expand migration(s) + permission seed applied; `alembic check` clean  
- [ ] Tests above green on real PG  
- [ ] PR CI green  
- [ ] Independent review; merge **only after** Phase 15.5 is LOCKED on main  
- [ ] Docs: checklist + master plan → Phase 16 CI VERIFIED / LOCKED (post-merge only)

---

## Architecture invariants (checklist for implementers)

1. **Domain → Outbox → Notification consumer → Adapter** — never Domain → Adapter.  
2. **No generic public `/inbox`.** Provider webhooks later, adapter-normalized only.  
3. **Federation ≠ Tenant**; notifications/reports are **per Gym (tenant)**.  
4. **IsolationProvider / RLS** remains on all new/expanded tenant tables.  
5. **Transactional Outbox** + delivery/run dedupe for at-least-once → effectively-once business effects (do not claim global exactly-once).  
6. **No raw card data** in notification context payloads; no float money in report financial fields.  
7. Prefer **ADR** if replacing outbox spine with a bus (Kafka/SQS still deferred).

---

## Suggested package layout

```text
backend/app/models/notification.py
backend/app/models/report.py
backend/app/services/notification.py
backend/app/services/notification_providers.py
backend/app/services/report.py
backend/app/api/v1/endpoints/notifications.py   # 16E/API wave
backend/app/api/v1/endpoints/reports.py
backend/app/core/event_types.py                 # register Phase 16 types
backend/tests/services/test_notification.py
backend/tests/services/test_report.py
```

---

## Deferred beyond Phase 16

- Real multi-channel provider SDKs and delivery webhooks  
- Encrypted export store + signed URLs  
- Scheduled reports / job scheduler productization  
- Full `/me` member-facing notification preferences  
- Kafka/SQS bus adapters  
- Standalone worker process (in-process / test harness acceptable for MVP)

---

## Merge order (non-negotiable)

```text
main (Phase 8–15 LOCKED)
  → Phase 15.5 PR merge + main CI → LOCKED
  → Phase 16 PR (this plan) merge + main CI → LOCKED
  → Phase 17 routers completion / gap fill
```

Stacked development on `feat/phase16-notifications-reports` is allowed **on top of** 15.5 work; formal GO for merge is **after** 15.5 LOCKED.
