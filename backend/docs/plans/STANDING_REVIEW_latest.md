# Standing Review — latest

**Date:** 2026-08-10  
**Branch:** `feat/phase16-notifications-reports` (includes uncommitted/local tip)  
**Scope:** Mandatory deep-dive — Phase 15.5C/D trust, 15.6 residual, Phase 16 full paths, claimed P2 burns, tests vs claims, docs truth  
**Protocol:** `backend/docs/plans/STANDING_REVIEW_PROTOCOL.md`  
**Reviewer:** Mandatory deep-dive review agent (code-first; no merge / no branch protection change)  
**Pytest this run:** **Not executed** (no agent shell; Postgres host default in conftest is `:5432`, compose maps **5433**). Orchestrator **must** re-run focused suite before any “tests green / ready” claim.

---

## Verdict

### **PASS_WITH_P2**

Core integrity and Phase 16 delivery paths match code on this branch. Prior integrity P0/P1 items remain closed. Claimed P2 burns (**report FAILED terminal + outbox raise**, **notification DEAD/CANCELLED no-raise**, **free-form address → write**, **handler consolidation**) are **present in code and mostly tested**.

**Not** PASS (clean): residual authz edge, report “retry” semantics without redrive, stale residual docs, ops CLI unit-test mock likely wrong, formal process gates open, pytest not re-run here.

**Not** NEEDS_WORK / BLOCKED: no open P0/P1 product correctness hole found against 15.5C/D + Phase 16 hard rules. Prefer not to inflate to FAIL.

**Do not claim:** Phase 15.5/16 LOCKED, CI VERIFIED on main, or production-ready.

**Mandatory review gate: PASS required before next feature batch**  
This review is **PASS_WITH_P2** — next **feature** batch allowed only if residual P2s stay logged and formal merge order (15.5 before 16) is not violated. Do **not** treat as green light to claim LOCKED or skip re-running pytest.

---

## Context

| Item | State (code / docs) |
|------|---------------------|
| Main | Phase 8–15 LOCKED (`af8f809` per checklist) |
| PR #25 Phase 15.5 | CI green claimed in checklist — **not LOCKED** (APPROVE + merge + main CI open) |
| Phase 15.6 | Ops residual **DONE on branch** — **not LOCKED** |
| PR #26 Phase 16 | Stacked WIP — **not LOCKED** |
| Alembic head (branch) | `q0d1e2f3a4b5_phase16_notifications_reports` |
| Public outbox source | **Absent** (`endpoints/outbox.py` gone); **stale** `outbox.cpython-312.pyc` still in `__pycache__` |

---

## Correctness matrix (file:line evidence)

### 1) Phase 15.5C/D trust

| Check | Result | Evidence |
|-------|--------|----------|
| No public `/outbox` / `/inbox` inject | **PASS** | `app/api/v1/api.py:16-31` — routers: memberships…notifications, reports, me; comment L30. No `outbox` under `endpoints/*.py`. Tests: `tests/api/test_phase15_5c_trust_boundaries.py:100-114` (404). |
| `*:self` + `require_self` | **PASS** | `app/core/authorization.py:151-153`, `224-231`, `247-290` (`require_tenant` rejects `:self`; `require_self` requires owner). Used: `app/api/v1/endpoints/me.py:54-58`, `access.py` issue-self. MEMBER YAML: self-only perms, no `notifications:*`/`reports:*` (`permissions.yml`). |
| Event registry allowlist | **PASS** | `app/core/event_types.py:17-18` multi-segment pattern; `38-41`, `53-55` register `notification.requested.v1` + `report.run.requested.v1`; `74-90` validate + deny unknown. Enforced: `app/services/outbox.py:64-65`. |
| Outbox max_attempts → DEAD | **PASS** | `app/services/outbox.py:136-170` stale PROCESSING ≥ max → DEAD; `172-216` claim filter `attempt_count < max_attempts`; defensive L203-208; `mark_failed` L266-267. Tests: `tests/services/test_outbox_max_attempts.py`. |

### 2) Phase 15.6 residual

| Check | Result | Evidence |
|-------|--------|----------|
| Dedupe HTTP 201 create / 200 hit | **PASS** | `endpoints/notifications.py:205-207`; `endpoints/reports.py:160-162`. API: `test_delivery_and_run_dedupe_returns_200`. |
| `process_due_failed` ops surface | **PASS (MVP)** | Service: `notification.py:333-369`. CLI: `scripts/process_notification_due.py`. Docs: `phase15_6_residual_closeout.md`. **No** public HTTP (correct). |
| Ops CLI unit tests | **P2 / likely broken** | `tests/scripts/test_process_notification_due.py:35-36` patches `scripts.process_notification_due.NotificationService`, but CLI **local-imports** `app.services.notification.NotificationService` (`process_notification_due.py:44`). Patch target is wrong → AttributeError or no mock of real path. **Orchestrator must confirm with pytest.** |

### 3) Phase 16 — notification path

```text
POST /notifications/deliveries
  → authz: send (user_id) | write (address-only)
  → schedule_delivery(..., enqueue_outbox=True)  # HTTP hardcodes True
  → same-TX OutboxService.enqueue(notification.requested.v1)
  → claim_pending → outbox_notification_requested_handler
  → dispatch_delivery → provider
  → SENT/CANCELLED/DEAD: handler return → mark_published
  → FAILED: raise notification_delivery_not_sent → mark_failed
```

| Step | Result | Evidence |
|------|--------|----------|
| HTTP always enqueues | **PASS** | Schema omits `enqueue_outbox` (`notifications.py:53-64`); endpoint L201. |
| Recipient tenant bind | **PASS** | `notification.py:166-176` `UserRole` + `recipient_not_in_tenant`. |
| Free-form address length | **PASS** | L159-164 empty/too long. |
| Fail → DEAD | **PASS** | L294-319; tests fail→DEAD + process_due. |
| Handler raise policy IR-007 | **PASS (updated)** | L394-406: SENT/CANCELLED/DEAD no raise; else raise. Tests: `test_outbox_handler_does_not_raise_on_dead_or_cancelled`, `test_outbox_handler_dead_delivery_marks_outbox_published`, `test_outbox_handler_raises_on_failed_delivery_marks_outbox_failed`. |
| Dual handler IR-006 | **PASS (consolidated)** | Instance `handle_notification_requested` L323-331 delegates to module handler; shared `_extract_notification_delivery_id` L372-386. Residual: instance ignores `_db`, uses `self.db`. |
| Free-form write IR-004 | **PASS (MVP policy)** | Endpoint L176-185: address-only → `notifications:write`; `recipient_user_id` → `notifications:send`. API tests `test_ir004_*`. |
| IR-004 residual | **P2** | If **both** `recipient_user_id` **and** free-form `recipient_address` set, only **send** is required → send-only roles can still attach arbitrary address. Policy text says “address only”; full harden would require write whenever `recipient_address` is non-null. **No test for dual-field body.** |
| Domain boundary | **PASS** | Membership ↛ providers: `tests/test_architecture.py:128-169`. Bridge exists, not imported by membership: `notification_bridge.py:13-15`. |

### 4) Phase 16 — report path

```text
POST /reports/runs → request_run(enqueue_outbox=True)
  → outbox report.run.requested.v1
  → outbox_report_run_requested_handler → execute_run
  → SUCCEEDED/CANCELLED: no raise → mark_published
  → FAILED: raise report_run_failed → mark_failed
```

| Step | Result | Evidence |
|------|--------|----------|
| Event type registered | **PASS** | `event_types.py:40,55`; enqueue via `report.py:146-156`. |
| Terminal SUCCEEDED/CANCELLED | **PASS** | `report.py:179-180`. |
| FAILED terminal unless redrive | **PASS** | L181-183; test `test_execute_run_failed_and_cancelled_are_terminal_without_redrive`. |
| Outbox raise on FAILED | **PASS (as designed)** | Handler L231-232; tests raise + mark_failed. |
| Outbox redelivery re-executes? | **P2 latent** | Handler always `execute_run(..., redrive=False)` L230. After first FAILED, outbox retries only re-raise until outbox DEAD — **no re-execution**. Raise prevents false PUBLISHED ACK; it does **not** implement true export redrive. Comment L215-218 admits this. Acceptable MVP only while executor is placeholder success. |
| Money floats | **N/A / OK** | `row_count` int; no amount fields on report models. |

### 5) Authz / tenancy / money / docs

| Check | Result | Evidence |
|-------|--------|----------|
| MEMBER denied staff notif/report | **PASS** | YAML MEMBER lacks grants; API 403 suites. |
| send ≠ write | **PASS (MVP)** | YAML MANAGER/FRONT_DESK send without write; endpoints enforce per verb + IR-004. |
| Tenancy filters + RLS tables | **PASS (MVP)** | Services filter `tenant_id`; RLS enable since operational MVP migration; `test_phase16_tenancy_isolation.py` (+ optional GUC). |
| Docs LOCKED / production | **PASS (no false LOCKED on checklist)** | `PROGRESS_CHECKLIST.md`: 15.5 not LOCKED; 16 IN PROGRESS; production-ready forbidden. |
| Residual docs drift | **P2** | Multiple plans still list IR-002/003/004/006/007 as open while code closed them (see Docs drift). Plan exit checkbox understates existing architecture + RLS tests (`phase16_notifications_reports.md:283`). |

---

## Claimed P2 burns — status

| Burn | Code status | Tests |
|------|-------------|-------|
| Report FAILED terminal + outbox raise | **Implemented** (`report.py:181-183`, `231-232`) | Service tests present |
| Notification DEAD/CANCELLED no raise; FAILED raises | **Implemented** (`notification.py:401-406`) | Dedicated IR-007 tests |
| Free-form address requires `notifications:write` | **Implemented** for address-only HTTP (`notifications.py:182-185`) | IR-004 API tests; dual-field hole open |
| Dual handler cleanup | **Implemented** (delegate + shared extract) | `test_handle_notification_requested_shares_parse_and_raise_policy` |

---

## Incorrect / incomplete implementations

**None at P0/P1 product integrity** for the mandatory checklist (public outbox, `*:self`, registry, max DEAD, schedule→outbox→provider, recipient bind, MEMBER denial).

### Residual incorrect / incomplete (P2)

1. **IR-004 incomplete when both recipient fields set** — send-only can still free-form blast if `recipient_user_id` present (`notifications.py:182-185`).  
2. **Report outbox “retry” does not redrive execution** — terminal FAILED + raise burns outbox attempts without `redrive=True` (`report.py:230-232`). Misleading if docs say “retry alive” = re-execute.  
3. **Ops CLI unit tests likely incorrect** — wrong mock path (`tests/scripts/test_process_notification_due.py` vs local import in CLI).  
4. **`handle_notification_requested` ignores `_db`** — always `self.db` (`notification.py:323-331`).  
5. **Stale bytecode** — `endpoints/__pycache__/outbox.cpython-312.pyc` after source removal.  
6. **Docs residual lists stale** — claim open burns that code closed; plan exit criteria still checks off architecture/RLS as missing.  
7. **Domain → notification bridge not production-wired** — helper + tests only; membership.activated consumer deferred (OK if documented; not a silent shortcut).  

---

## Tests inventory vs claims

| Claimed coverage | Path | Present? |
|------------------|------|----------|
| Notification service (render, dedupe, outbox, fail/DEAD, process_due, recipient bind, IR-007) | `tests/services/test_notification.py` | **Yes** |
| Report service (outbox, terminal, raise) | `tests/services/test_report.py` | **Yes** |
| Tenancy isolation + RLS GUC | `tests/services/test_phase16_tenancy_isolation.py` | **Yes** |
| API RBAC MEMBER 403 | `tests/api/test_notifications_reports_rbac.py` | **Yes** |
| API schedule/dedupe/IR-004 | `tests/api/test_phase16_notifications_reports.py` | **Yes** |
| Architecture Membership ↛ notification | `tests/test_architecture.py` | **Yes** |
| Event registry | `tests/core/test_event_types.py` | **Yes** |
| 15.5C public outbox absent | `tests/api/test_phase15_5c_trust_boundaries.py` | **Yes** |
| Outbox max-attempt DEAD | `tests/services/test_outbox_max_attempts.py` | **Yes** |
| NotificationBridge | `tests/services/test_notification_bridge.py` | **Yes** |
| process_due CLI | `tests/scripts/test_process_notification_due.py` | **Present; mock path suspect** |
| Dual-field free-form + send | — | **Missing** |
| Report true redrive via outbox handler | — | **Missing (by design gap)** |

**This review did not re-execute pytest.** Do not claim suite green from this document alone.

### Suggested focused pytest (orchestrator)

```bash
cd backend
export TEST_DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:5433/fnos_review_mand'
export TEST_RUNTIME_DATABASE_URL='postgresql+asyncpg://app_user:app_password@localhost:5433/fnos_review_mand'
# create DB if needed, then:
uv run pytest \
  tests/services/test_notification.py \
  tests/services/test_report.py \
  tests/services/test_notification_bridge.py \
  tests/services/test_phase16_tenancy_isolation.py \
  tests/services/test_outbox_max_attempts.py \
  tests/api/test_notifications_reports_rbac.py \
  tests/api/test_phase16_notifications_reports.py \
  tests/api/test_phase15_5c_trust_boundaries.py \
  tests/test_architecture.py \
  tests/core/test_event_types.py \
  tests/scripts/test_process_notification_due.py \
  -q
```

---

## Docs drift (LOCKED claims false?)

| Doc | Drift? |
|-----|--------|
| `docs/PROGRESS_CHECKLIST.md` | **Mostly honest** — 15.5/16 not LOCKED; production-ready forbidden. Residual line still lists free-form/dual-handler/report FAILED as open P2 though **code largely closed** those. |
| `AGENTS.md` | Active still Phase 15.5 (process-true); date 2026-08-09 slightly stale vs Phase 16 stacked WIP. |
| `INTEGRITY_REVIEW_phase16_closeout.md` | Residual IR-002…007 table **stale** vs current code. |
| `phase15_6_residual_closeout.md` L80-89 | Same residual list **stale**. |
| `phase16_review_findings.md` P16-011/012/014 | **Stale** (CANCELLED terminal, dual handler, 201 dedupe closed). |
| `phase16_notifications_reports.md:283` | Exit checkbox still open for RLS + architecture tests that **exist**. |
| Prior `STANDING_REVIEW_latest.md` | **Stale** — listed IR-002/004/006/007 open; this review supersedes. |

**No false “LOCKED / production-ready” claim found on checklist for 15.5/16.**

---

## Formal gates still open

1. **Phase 15.5** independent APPROVE → merge → main CI → docs **LOCKED**  
2. **Phase 16** must **not** merge ahead of 15.5 LOCKED  
3. **Phase 16 PR CI** full green (this review is not CI)  
4. Do **not** mark Phase 16 LOCKED / CI VERIFIED / production-ready from this review  
5. Production notification reliability requires scheduled `process_due_failed` (+ real providers)  
6. **Re-run focused pytest** on isolated DB before any batch “done” claim  
7. **Mandatory review gate: PASS required before next feature batch** (this file = PASS_WITH_P2)

---

## Dimension summary

| Dimension | Status |
|-----------|--------|
| Public outbox inject | **OK** — absent (stale pyc hygiene only) |
| MEMBER `*:self` / BOLA | **OK** |
| Event registry + multi-segment report type | **OK** |
| Outbox max-attempt DEAD | **OK** |
| Notification schedule → outbox → SENT/FAILED/DEAD | **OK** |
| Report request → outbox → SUCCEEDED; FAILED raise | **OK (MVP; no true redrive)** |
| IR-004 free-form write | **OK address-only; P2 dual-field** |
| IR-006/007 handler policy | **OK** |
| 15.6 201/200 + ops docs | **OK** |
| Domain Membership ↛ providers | **OK** |
| Tests vs claims | **Mostly OK; CLI unit mock suspect; dual-field untested** |
| Docs residual truth | **P2 drift** |
| Formal LOCKED / production | **Open process** |

---

## Final statement

**Verdict: PASS_WITH_P2**

Code on `feat/phase16-notifications-reports` holds 15.5C/D trust boundaries and Phase 16 Domain → Outbox → Handler → Adapter paths. Claimed P2 burns are largely landed and tested. Residual P2s (dual-field free-form, report redrive semantics, CLI test mock, docs drift) must not be waved into LOCKED or production-ready. **Mandatory review gate: PASS required before next feature batch** — satisfied at PASS_WITH_P2 only if next work is residual burn-down / CI / merge process, not a silent skip of formal gates.

---

## Orchestrator rule

After every agent/human batch: run this review agent before commit/push claim of done.

```text
Implement → focused tests → Standing Review → fix if NEEDS_WORK/BLOCKED → commit/push
```

Do **not** skip Standing Review to “save time.”  
Overwrite `backend/docs/plans/STANDING_REVIEW_latest.md` each run with a new dated review.
