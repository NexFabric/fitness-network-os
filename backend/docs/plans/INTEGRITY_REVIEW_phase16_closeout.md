# FINAL INTEGRITY REVIEW — Phase 16 closeout

**Workspace:** `/Users/emrah/GymClubNex`  
**Branch:** `feat/phase16-notifications-reports`  
**Review type:** Read-only integrity (code truth)  
**Date:** 2026-08-10  
**Scope:** Uncommitted + Phase 16 committed work on this branch; trust-boundary regressions from Phase 15.5 that Phase 16 must not undo  

**Out of scope / non-claims:**

- This document does **not** claim Phase **15.5 LOCKED**.
- This document does **not** claim Phase **16 LOCKED** or **CI VERIFIED**.
- This document does **not** claim **production-ready**.
- No code fixes applied in this review (document only).

---

## Verdict: **CLEAN**

All **must-verify** integrity items below are present and consistent with code on this branch.  
Residual issues are **P2 hygiene / ops / formal process**, not open P0/P1 integrity holes against the required checklist.

Phase 16 remains safe to document as **IN PROGRESS on branch only** — **not LOCKED**, **not merge-ready ahead of Phase 15.5 LOCKED on `main`**.

---

## Must-verify matrix (code truth)

| # | Check | Result | Evidence |
|---|--------|--------|----------|
| 1 | No public `/outbox` routes | **PASS** | `app/api/v1/api.py` includes notifications/reports/me only; comment documents Phase 15.5C removal. No outbox/inbox routers under `endpoints/`. |
| 2 | MEMBER `*:self` + `require_self` still present | **PASS** | `AuthorizationService.is_self_permission` / `require_self` / `require_tenant` in `app/core/authorization.py`. Used by `/me/entitlements/check` and `/access/qr/issue-self`. MEMBER YAML grants remain self-only (`permissions.yml` `MEMBER`: no `notifications:*` / `reports:*`). |
| 3 | Event registry includes `report.run.requested.v1` | **PASS** | `REPORT_RUN_REQUESTED_V1 = "report.run.requested.v1"` registered in `_EVENT_TYPE_SPECS` / `REGISTERED_EVENT_TYPES`; multi-segment `EVENT_TYPE_PATTERN` allows it; `validate_event_type` enforces registry. |
| 4 | Outbox claim max_attempts → DEAD | **PASS** | `OutboxService.claim_pending`: stale PROCESSING with `attempt_count >= max_attempts` → `DEAD` + `max_attempts_exceeded_on_claim`; claim filter `attempt_count < max_attempts`; defensive in-loop DEAD. Covered by `tests/services/test_outbox_max_attempts.py`. |
| 5 | Phase 16: HTTP schedule/run always `enqueue_outbox=True` | **PASS** | HTTP schemas omit `enqueue_outbox` (`DeliveryScheduleRequest`, `RunRequest`). Endpoints hardcode `enqueue_outbox=True`. Flag remains service-internal for unit tests. API test: body without field accepted. |
| 6 | `recipient_user_id` tenant `UserRole` check | **PASS** | `NotificationService.schedule_delivery`: if `recipient_user_id` set, requires `UserRole` with matching `user_id` + `tenant_id` else `recipient_not_in_tenant`. Tested in `tests/services/test_notification.py`. |
| 7 | Outbox handler raises if delivery not SENT | **PASS** | `outbox_notification_requested_handler` and `handle_notification_requested` raise `RuntimeError("notification_delivery_not_sent:...")` when status ≠ `SENT` after `dispatch_delivery`. Test: `test_outbox_handler_raises_on_failed_delivery_marks_outbox_failed`. |
| 8 | Migration `q0` exists with permission seed | **PASS** | `alembic/versions/q0d1e2f3a4b5_phase16_notifications_reports.py`: expand columns + indexes; seeds `notifications:read/write/send`, `reports:read/write/run` and role grants (GYM_OWNER/ADMIN/MANAGER, ACCOUNTANT, FRONT_DESK). YAML parity in `permissions.yml`. |
| 9 | Tests: notification, report, tenancy, API RBAC, architecture boundary | **PASS** | See test inventory below. |
| 10 | No obvious BOLA / tenancy holes on new endpoints | **PASS (MVP)** | Staff endpoints use `require_tenant` + `X-Tenant-ID` membership check; all service queries filter `tenant_id`; get-by-id scoped by tenant; MEMBER denied staff surfaces (API 403 tests). Residual staff free-form address is intentional MVP (not member BOLA). |

---

## Test inventory (item 9)

| Area | Path | Covers |
|------|------|--------|
| Notification service | `tests/services/test_notification.py` | render, dedupe, outbox enqueue, provider SENT, fail→DEAD, `process_due_failed`, `recipient_not_in_tenant`, handler raise → outbox FAILED |
| Report service | `tests/services/test_report.py` | definition, request_run + outbox `report.run.requested.v1`, execute, dedupe, outbox dispatch → SUCCEEDED |
| Tenancy isolation | `tests/services/test_phase16_tenancy_isolation.py` | cross-tenant templates/deliveries/definitions/runs; service wrong-tenant not found; optional `app.current_tenant_id` RLS GUC |
| API RBAC | `tests/api/test_notifications_reports_rbac.py` | MEMBER 403 on notifications/reports staff routes |
| API happy / contract | `tests/api/test_phase16_notifications_reports.py` | staff create template/definition; schedule body without `enqueue_outbox` |
| Architecture membership boundary | `tests/test_architecture.py` | Membership must not import notification providers / notification service |
| 15.5 trust (regression) | `tests/api/test_phase15_5c_trust_boundaries.py` | public outbox routes absent; MEMBER self entitlement BOLA |
| Outbox max-attempt | `tests/services/test_outbox_max_attempts.py` | claim DEAD / crash-loop |

---

## Residual issues (non-blocking for this checklist)

| ID | Sev | Issue | Notes |
|----|-----|-------|-------|
| IR-001 | **P2** **CLOSED (15.6)** | HTTP returns **201** even when dedupe returns `created=False` | **CLOSED:** `POST /deliveries` and `POST /runs` set 201 if created else 200; API test `test_delivery_and_run_dedupe_returns_200`. |
| IR-002 | **P2** | Report outbox handler does **not** raise on `FAILED` | `execute_run` swallows exceptions → FAILED; outbox still `mark_published`. Report retry depends on re-drive policy not implemented. Acceptable for MVP placeholder export. |
| IR-003 | **P2** | `execute_run` can re-drive terminal **FAILED** | Early-return for SUCCEEDED/CANCELLED only; FAILED can become RUNNING again on redelivery. |
| IR-004 | **P2** | Free-form `recipient_address` allowed for staff with `notifications:send` | By design for MVP; `recipient_user_id` is tenant-bound. Production harden: bind address to member/contact or restrict free-form to higher roles / internal callers. |
| IR-005 | **P2** **DOCUMENTED (15.6)** | `process_due_failed` has no cron/worker/HTTP surface | Mitigated for outbox path: handler raise keeps outbox retry alive. **15.6:** documented as **required ops job** before production reliability claims (`phase15_6_residual_closeout.md`). Product cron still deferred. |
| IR-006 | **P2** | Dual notification handlers (`handle_notification_requested` + module `outbox_notification_requested_handler`) | Both raise on non-SENT; still duplicated parse logic — keep one path long-term. |
| IR-007 | **P2** | After delivery **DEAD**, handler still raises → outbox burns remaining attempts | Correct eventual DEAD on outbox; slightly wasteful. Optional: treat delivery DEAD as handler success or short-circuit. |
| IR-008 | **Process** | Formal PR CI green + Phase 15.5 human APPROVE/merge not part of this review | Checklist docs still show 15.5 awaiting APPROVE; Phase 16 merge **after** 15.5 LOCKED only. |

No **P0/P1** integrity regressions found against the must-verify list.

---

## What is safe to document as IN PROGRESS (branch) vs NOT LOCKED

### Safe to document as **IN PROGRESS on `feat/phase16-notifications-reports`**

- 16A: models + expand migration `q0d1e2f3a4b5` + event registry + permission seed/YAML  
- 16B: schedule → same-TX outbox (`notification.requested.v1`) → handler → dispatch; HTTP always enqueues; non-SENT raises  
- 16C: log provider adapters only (no real WhatsApp/SMS SDK)  
- 16D: report definitions/runs MVP (metadata + `memory://` placeholder export)  
- 16E **MVP tests present** on branch (service + API RBAC + tenancy isolation + architecture boundary)  
- Integrity closeout items **1–10** above: **code-pass** on this branch  

### Must **not** document as LOCKED / CI VERIFIED / production-ready

| Claim | Status |
|-------|--------|
| Phase **15.5 LOCKED** | **No** — process gate open (PR APPROVE → merge → main CI → docs LOCKED) |
| Phase **16 LOCKED** | **No** |
| Phase 16 **CI VERIFIED** | **No** (this review did not re-run full CI; do not self-declare) |
| Production-ready notifications/reports | **No** — log adapters, placeholder report export, no scheduled delivery worker, residual P2s |
| Safe to merge Phase 16 to `main` ahead of 15.5 | **No** — merge order: **15.5 LOCKED first**, then Phase 16 |

### Explicit non-claims

- Do **not** claim Phase 15.5 LOCKED based on this review.  
- Do **not** claim production-ready.  
- Do **not** treat prior `phase16_review_findings.md` “NEEDS_WORK for formal gates” as contradiction of this **CLEAN** integrity checklist — formal merge gates remain open; **integrity must-verify items are closed in code**.

---

## Dimension summary

| Dimension | Status |
|-----------|--------|
| Public outbox inject surface | **OK** — absent |
| MEMBER least privilege / `*:self` | **OK** — preserved |
| Event registry + multi-segment report type | **OK** |
| Outbox max-attempt DEAD | **OK** |
| HTTP always enqueues outbox | **OK** |
| Recipient tenant bind (`UserRole`) | **OK** |
| Delivery non-SENT → outbox retry | **OK** |
| Migration + RBAC seed | **OK** |
| Tenancy filters + RLS tables (pre-existing enable) + isolation tests | **OK (MVP)** |
| Domain boundary Membership ↛ providers | **OK** + architecture tests |
| Formal LOCKED / production | **Open process / deferred** |

---

## Recommended next process steps (no code required for integrity)

1. Keep Phase 16 branch stacked; **do not merge** until Phase 15.5 is **LOCKED on `main`**.  
2. Run formal PR CI (security / lint / unit+integration) on this branch before any merge attempt.  
3. Optionally burn down residual P2s (201-on-dedupe, report FAILED redrive, single outbox handler, free-form address policy) in a follow-up commit — **not blockers** for this integrity closeout checklist.  
4. Only after merge + main CI green may docs move Phase 16 toward **CI VERIFIED / LOCKED** (never from this document alone).

---

## Final statement

**Verdict: CLEAN** — mandatory integrity checklist **PASS** against current code on `feat/phase16-notifications-reports`.  

**Document as:** Phase 16 **IN PROGRESS** on branch.  
**Do not document as:** 15.5 LOCKED, 16 LOCKED, CI VERIFIED, or production-ready.
