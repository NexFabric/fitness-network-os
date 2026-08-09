# Standing Review — post 15.5 merge + lock docs + stack + 21–26 open

**Date:** 2026-08-10  
**Reviewer role:** mandatory independent standing review (code + git + GitHub API)  
**Scope:** main after PR #25; PR #27 lock docs; PR #26 stack (16–20 + 21–26 start); CI posture  
**Verdict:** 🟠 **NEEDS_WORK** (not merge-ready for #26 until full CI green + human review)

Do **not** claim production-ready. Do **not** mark Phase 16–26 LOCKED. Phase 26 exit gate **NOT PASSED**.

---

## Executive summary

| Item | Live truth | Notes |
|------|------------|-------|
| Phase 15.5 **code on main** | ✅ `125a8c6` | PR #25 merged; alembic head `p9c0d1e2f3a4` |
| Phase 15.5 **main post-merge CI** | ✅ **success** | Run `31340441176` completed success (Security, Lint, Unit/Integration) |
| Phase 15.5 **formal lock docs on main** | 🟡 **PR #27 open** | Docs branch claims LOCKED; land #27 to update main docs |
| PR #26 base | ✅ `main` | Retargeted; mergeable when CI green |
| PR #26 content | 16–20 + 21–26 start | Notifications/reports through scanner; CI V2 FE jobs; container/HTTP/obs stubs |
| Public outbox | ✅ absent | 15.5C retained; notifications use domain → event → delivery path |
| False LOCK 16–26 | ✅ none | Branch labels IMPLEMENTED / starting — not LOCKED |
| Production-ready | ❌ no | Phase 26 gate NOT PASSED |

---

## Mandatory checklist

| # | Check | Result | Evidence |
|---|--------|--------|----------|
| 1 | Phase 15.5 on main (`125a8c6`) | **PASS** | Merge PR #25; migrations `n7`/`o8`/`p9`; head `p9c0d1e2f3a4` |
| 2 | Lock docs (15.5 only) after green main CI | **PASS (branch/PR)** / **pending main** | Main CI green for merge run. PR [#27](https://github.com/NexFabric/fitness-network-os/pull/27) documents 🟢 LOCKED. Main tree still stale until #27 merges. **Do not lock 16–20.** |
| 3 | PR #26 base = `main` | **PASS** | `base.ref=main`, base SHA `125a8c6` lineage |
| 4 | Phase 21 CI V2 does not break backend | **PASS (design)** / **CI watch** | Backend jobs unchanged. Added parallel `Admin Web Build` + `Scanner PWA Build` (`npm ci` + build). FE builds green on PR runs observed. |
| 5 | No public outbox reintroduced | **PASS** | No `/outbox` public router; stack adds `/notifications`, `/reports`, `/me` only |
| 6 | No false production-ready / false LOCK 16–26 | **PASS** | Checklist + phase26 plan: **NOT PASSED**; 16–26 not LOCKED |

---

## Batch results

### A — Phase 15.5 LOCKED docs

| Item | Status |
|------|--------|
| Main merge SHA | `125a8c6` |
| Alembic head | `p9c0d1e2f3a4` |
| Docs PR | [#27](https://github.com/NexFabric/fitness-network-os/pull/27) `chore/phase15-5-locked-docs` |
| Files | `PROGRESS_CHECKLIST`, `REVIEW_CHECKPOINT`, `IMPLEMENTATION_MASTER_PLAN`, `phase15_5_integrity_closure.md` |
| Note | Stack tip also carries lock-language docs; formal main truth lands via #27 |

### B — Retarget / rebase Phase 16–20 stack

| Item | Status |
|------|--------|
| Branch | `feat/phase16-notifications-reports` |
| PR | [#26](https://github.com/NexFabric/fitness-network-os/pull/26) |
| Base | **`main`** (retargeted) |
| Merge-base | `125a8c6` (on 15.5) |
| Mergeable | yes when required checks green |

### C — Phase 21 CI V2 start

| Item | Status |
|------|--------|
| Plan | `backend/docs/plans/phase21_ci_v2.md` |
| Jobs | `Admin Web Build`, `Scanner PWA Build` in `.github/workflows/ci.yml` |
| Backend jobs | **intact** (security, lint/mypy, tenancy, permissions, pytest, alembic) |
| FE build (local) | admin-web + scanner-pwa `tsc && vite build` succeeded |
| LOCKED | **no** |

### D — Phase 22–23 skeleton

| Item | Status |
|------|--------|
| Phase 22 plan | `phase22_container_hardening.md` |
| Phase 22 code | `backend/Dockerfile.prod` multi-stage, non-root, no `--reload`; dev Dockerfile unchanged |
| Phase 23 plan | `phase23_http_security.md` |
| Phase 23 code | `ENVIRONMENT` + `CORS_ORIGINS`; production fail-closed CORS; `SecurityHeadersMiddleware` |
| Tests | `tests/core/test_config_cors.py` |
| LOCKED | **no** |

### E — Phase 24–26 open (light, not LOCKED)

| Phase | Artifact | Status |
|-------|----------|--------|
| 24 | `RequestLoggingMiddleware` + plans + tests | stub IMPLEMENTED on branch |
| 25 | `phase25_checklist_truth.md` | plan only |
| 26 | `phase26_core_mvp_exit_gate.md` | criteria only — **NOT PASSED** |

---

## Integrity non-negotiables (spot check)

- Money: `amount_minor` / no float money path reintroduced in 16–23 work  
- Tenancy/RLS gates still in CI  
- No public generic outbox/inbox  
- Domain → Event → Notification path (no Membership → WhatsApp shortcut)

---

## What blocks merge of PR #26

1. **Full required CI green** on latest head (backend unit/integration + frontend builds + CodeQL)  
2. **Independent human APPROVE** (branch protection review count = 1)  
3. Prefer **#27 merged first** so main docs truth matches 15.5 LOCK before/with stack review  
4. Honest review of 16–20 product scope (not only CI green)

---

## Verdict

🟠 **NEEDS_WORK** — Process and integrity posture are largely correct:

- 15.5 is on main with green post-merge CI; lock docs PR open  
- Stack retargeted to main with meaningful 16–20 + 21–26 start  
- No false production-ready; no false LOCK of 16–26  
- Public outbox still gone  

**Not clean enough for “merge #26 now”** until current CI suite is fully green and a human reviews the large stack. Phase 26 remains **NOT PASSED**.
