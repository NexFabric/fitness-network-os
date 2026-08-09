# Standing Review — latest

**Date:** 2026-08-10  
**Branch:** `feat/phase16-notifications-reports`  
**SHA (P2 burn-down):** `574849b`  
**Scope:** Integrator deep-dive after residual P2 reliability + address-policy batch (IR-002/003/004/006/007)  
**Protocol:** `backend/docs/plans/STANDING_REVIEW_PROTOCOL.md`  
**Reviewer:** Integrator + deep-dive (second hat; focused pytest **executed**)  
**Pytest this run:** **48 passed** on isolated DB `fnos_p2_batch` (port 5433)

## Context

| Item | State |
|------|--------|
| Main | Phase 8–15 LOCKED (`af8f809` per checklist) |
| PR #25 Phase 15.5 | CI green, **not LOCKED** (APPROVE + merge open) |
| Phase 15.6 | Residual ops polish **DONE on branch** — not LOCKED |
| PR #26 Phase 16 | Stacked on 15.5; residual P2 reliability **CLOSED in code** — **not LOCKED** |
| Alembic (branch) | `q0d1e2f3a4b5_phase16_notifications_reports` |

## Verdict

### **PASS_WITH_P2**

Safe to leave on PR / continue formal CI. **No open P0/P1** on delivery or report paths. Residual items are **ops productization / formal process** only (product cron deferred; 15.5 merge gate open).  

**Do not claim:** LOCKED, CI VERIFIED, or production-ready.  
**Do not merge Phase 16 ahead of Phase 15.5 LOCKED.**

---

## Must-verify checklist

| # | Check | Result | Evidence |
|---|--------|--------|----------|
| 1 | Tenancy | **OK** | Service `tenant_id` filters; composite FKs; RLS + `test_phase16_tenancy_isolation.py` |
| 2 | Authz / BOLA | **OK** | MEMBER denied staff surfaces; IR-004 free-form address needs `notifications:write`; `recipient_user_id` needs `notifications:send` + tenant `UserRole` |
| 3 | Money | **N/A** | No float money; report `row_count` int; placeholder export |
| 4 | Events | **OK** | No public outbox/inbox; registered `notification.requested.v1` + `report.run.requested.v1` |
| 5 | Domain boundaries | **OK** | Membership ↛ `notification*`; `NotificationBridge` is orchestrator helper only |
| 6 | Docs truth | **OK** | Phase 15.5/16 not LOCKED; not production-ready |
| 7 | Tests | **OK** | 48 passed focused suite including IR-002/003/004/006/007 + bridge + ops CLI |

---

## Deep-dive path traces

### 1) Notification delivery path

```text
POST /api/v1/notifications/deliveries
  → if recipient_user_id: require_tenant(notifications:send)     # IR-004
  → else (address-only): require_tenant(notifications:write)     # IR-004
  → NotificationService.schedule_delivery(..., enqueue_outbox=True)
       channel validation; address length; UserRole tenant bind
       INSERT delivery QUEUED + same-TX outbox notification.requested.v1
  → 201 if created else 200

Worker:
  claim_pending → outbox_notification_requested_handler          # IR-006
    → _extract_notification_delivery_id (shared parse)
    → dispatch_delivery FOR UPDATE
         SENT | CANCELLED | DEAD → handler success (no raise)    # IR-007
         FAILED / other → raise notification_delivery_not_sent
           → OutboxService.mark_failed (retry/backoff)

Ops dual path (IR-005 mitigated):
  scripts/process_notification_due.py <tenant_uuid>
    → SET LOCAL app.current_tenant_id + process_due_failed
```

| Step | Assessment |
|------|------------|
| HTTP always enqueues | **Correct** |
| Free-form address policy | **Closed IR-004** — send-only 403 on address-only (API tests) |
| Shared handler / parse | **Closed IR-006** — instance method delegates to module handler |
| DEAD/CANCELLED no outbox burn | **Closed IR-007** — terminal → PUBLISHED |
| FAILED keeps outbox alive | **Correct** — raise → mark_failed |
| Domain bridge | **Helper only** — not imported from MembershipService |

### 2) Report run path

```text
POST /api/v1/reports/runs
  → require_tenant(reports:run)
  → request_run(..., enqueue_outbox=True) → report.run.requested.v1

Worker:
  outbox_report_run_requested_handler
    → execute_run(tenant_id, run_id)  # redrive=False default
         SUCCEEDED | CANCELLED → no-op
         FAILED + redrive=False → no-op (terminal)               # IR-003
         else → MVP memory:// SUCCEEDED (or FAILED on exception)
    → if status == FAILED: raise report_run_failed               # IR-002
         → mark_failed until max attempts
```

| Step | Assessment |
|------|------------|
| Raise on FAILED | **Closed IR-002** |
| Terminal FAILED without redrive | **Closed IR-003** — `redrive=True` required |
| Happy path | **OK** — PENDING → SUCCEEDED + memory URL |
| Note | Outbox redelivery of already-FAILED does not auto-redrive (explicit flag only); burns attempts until DEAD — acceptable for always-succeed MVP placeholder |

### 3) Authz (YAML + IR-004)

| Role | write | send | free-form address | tenant user_id |
|------|-------|------|-------------------|----------------|
| GYM_OWNER / ADMIN | yes | yes | yes | yes |
| GYM_MANAGER | no | yes | **403** | yes |
| FRONT_DESK | no | yes | **403** | yes |
| MEMBER | no | no | 403 | 403 |

---

## Residual P2 status after this batch

| ID | Status | Notes |
|----|--------|-------|
| IR-001 | **CLOSED (15.6)** | 201/200 dedupe |
| IR-002 | **CLOSED** | Report handler raises on FAILED |
| IR-003 | **CLOSED** | FAILED terminal unless `redrive=True` |
| IR-004 | **CLOSED** | Address-only → `notifications:write` |
| IR-005 | **MITIGATED** | Ops CLI `process_notification_due.py`; product cron still deferred |
| IR-006 | **CLOSED** | Single parse/raise via module handler + thin wrap |
| IR-007 | **CLOSED** | SENT/CANCELLED/DEAD → handler success |
| Process | **Open** | 15.5 APPROVE/merge; Phase 16 merge after 15.5 LOCKED; full PR CI |

---

## Formal gates still open

1. **Phase 15.5** independent APPROVE → merge → main CI → docs **LOCKED**  
2. **Phase 16** must **not** merge ahead of 15.5 LOCKED  
3. Full PR CI green before merge claim  
4. Do **not** mark Phase 16 LOCKED / CI VERIFIED / production-ready  
5. Production reliability still needs scheduled ops job + real providers  

---

## Test inventory (this run)

```text
tests/services/test_notification.py
tests/services/test_report.py
tests/api/test_phase16_notifications_reports.py
tests/api/test_notifications_reports_rbac.py
tests/services/test_phase16_tenancy_isolation.py
tests/test_architecture.py
tests/services/test_notification_bridge.py
tests/scripts/test_process_notification_due.py

→ 48 passed in ~122s (TEST_DATABASE_URL=…/fnos_p2_batch @ :5433)

Also gates: ruff check app tests scripts ✓ | mypy app ✓ | check_permissions.py ✓
```

---

## Dimension summary

| Dimension | Status |
|-----------|--------|
| Notification full path SENT/FAILED/DEAD | **OK** |
| Report request → outbox → SUCCEEDED / FAILED raise | **OK** |
| Authz MEMBER + IR-004 address policy | **OK** |
| Tenancy / RLS isolation | **OK** |
| Domain Membership ↛ providers | **OK** |
| Public outbox inject | **Absent** |
| Formal LOCKED / production | **Open process** |

---

## Final statement

**Verdict: PASS_WITH_P2** — residual reliability/address-policy P2s IR-002/003/004/006/007 **closed in code** with tests green on isolated PG.

**Document as:** Phase 16 **IN PROGRESS** on branch (P2 reliability batch at `574849b`).  
**Do not document as:** 15.5 LOCKED, 16 LOCKED, CI VERIFIED, or production-ready.
