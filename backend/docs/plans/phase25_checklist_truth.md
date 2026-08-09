# Phase 25 — Checklist Truth Model

**Status:** 🟠 **IMPLEMENTED on branch** (process + docs truth pass) — **not MERGED**; **not production-ready**  
**Date:** 2026-08-10  
**Plan path:** `backend/docs/plans/phase25_checklist_truth.md`  
**Source of maturity truth:** `docs/PROGRESS_CHECKLIST.md`  
**Exit gate companion:** `backend/docs/plans/phase26_core_mvp_exit_gate.md` (**FAIL / NOT PASSED**)  
**Do not claim:** production-ready (Phase 26 exit gate only)

---

## Purpose

Define **when** a phase or domain row may carry each maturity badge so agents and humans do not invent “LOCKED” / “production-ready” status from partial branch work.

Hierarchy (must not be inverted):

```text
MASTER_SPEC
  → PRODUCTION_READINESS
    → IMPLEMENTATION_MASTER_PLAN
      → PROGRESS_CHECKLIST   ← maturity truth for “what is done”
        → active phase plan (backend/docs/plans/phaseN_*.md)
```

Prefer **MERGED / IMPLEMENTED / PARTIAL** in new writing. Historical “LOCKED” means merge to `main` + green required CI.

---

## Maturity levels (canonical)

| Badge | Meaning | Allowed only when |
|-------|---------|-------------------|
| 📝 PENDING / NOT STARTED | Not started | Default for future work |
| ⬜ PLAN / skeleton / stub | Plan or thin spike only | Plan doc and/or minimal code; **no** merge claim |
| 🟡 MODEL | Schema / model present; service incomplete | Models + migrations may exist; product surface incomplete |
| 🟡 **PARTIAL** | Meaningful work landed; explicit gaps remain | Document gaps; never upgrade to MERGED without merge |
| 🟠 **IMPLEMENTED on branch** | Code present on feature branch | Feature exists in tree; **not** on main |
| 🟠 **IMPLEMENTED on main** / **MERGED** | Code on `main` | Merge SHA known |
| 🟢 CI VERIFIED | Required CI green for that change | Evidence: PR checks and/or main workflow |
| 🟢 CI VERIFIED / LOCKED | Phase closed on `main` | **Merge to `main` + green required CI** + checklist SHA |
| 🟢 PRODUCTION VERIFIED | Live/prod-grade acceptance | **Never** before Phase 26 exit gate **PASS** |

---

## Hard truth rules

1. **MERGED / LOCKED requires main.** Feature-branch “done” is at most 🟠 **IMPLEMENTED on branch** or 🟡 **PARTIAL**.  
2. **CI VERIFIED is evidence-based.** Point to PR number and/or merge SHA when promoting.  
3. **No production-ready claim** until Phase **26** exit gate is **PASS** (currently **FAIL / NOT PASSED**).  
4. **Domain rows lag services until promoted.**  
5. **Plans are not locks.** Presence of `phaseN_*.md` ≠ phase complete.  
6. **PROGRESS_CHECKLIST wins over chat memory** after a truth pass.  
7. **Deferred is not done.** “Known intentional deferrals” stay open.  
8. Prefer **IMPLEMENTED / PARTIAL / MERGED** over waiting on human lock rituals — but never upgrade to production-ready without Phase 26 PASS.

---

## Promotion recipe (phase merge)

1. Phase plan exit criteria checked with evidence.  
2. PR **merged to `main`**.  
3. Required main CI green.  
4. Update checklist + plan header + master plan row with merge SHA.  
5. **Do not** mark future phases MERGED by association.

---

## Opening honesty — stack status (2026-08-10)

| Phase | Honest status | Notes |
|-------|---------------|--------|
| 0–15 | 🟢 MERGED / CI VERIFIED on `main` | Domain track |
| 15.5 | 🟢 MERGED / CI VERIFIED on `main` | Merge `125a8c6` (PR #25); docs PR #27 |
| 16 | 🟠 **IMPLEMENTED on branch** | Notifications/reports; log provider; not on main |
| 17 | 🟡 **PARTIAL on branch** | 17A `/me/*` done; 17B/17C open |
| 18 | 🟡 **PARTIAL on branch** | Service-layer e2e; HTTP E2E deferred |
| 19–20 | 🟠 **IMPLEMENTED scaffold on branch** | Admin + scanner MVP shells |
| 21 CI V2 | 🟡 **PARTIAL on branch** | Frontend build jobs in `ci.yml` |
| 22 Container | 🟡 **PARTIAL on branch** | `Dockerfile.prod` multi-stage non-root |
| 23 HTTP security | 🟡 **PARTIAL on branch** | Prod CORS + basic headers |
| 24 Observability | 🟡 **PARTIAL stub on branch** | Request/correlation id + access log; no OTel |
| 25 Checklist truth | 🟠 **IMPLEMENTED on branch** | This doc + checklist/master plan sync |
| 26 Exit gate | 🔴 **FAIL / NOT PASSED** | See phase26 scorecard |

### Main vs PR #26

| Ref | Value |
|-----|--------|
| Main HEAD (15.5) | `125a8c6` |
| Alembic on main | `p9c0d1e2f3a4` |
| Stack branch | `feat/phase16-notifications-reports` |
| PR | [#26](https://github.com/NexFabric/fitness-network-os/pull/26) |
| Stack alembic | includes `q0d1e2f3a4b5` (Phase 16) |

---

## Anti-patterns (reject in review)

- Marking MERGED/LOCKED because tests pass locally only  
- Marking PRODUCTION VERIFIED because Compose runs  
- False MERGED/LOCKED on feature branch without main merge SHA  
- Claiming Phase 26 PASS while any required criterion is FAIL/PARTIAL  
- “Basically done” narrative instead of checklist bands  
- Treating light 21–24 stubs as production hardening complete  

---

## Phase 25 deliverables

| # | Deliverable | Status |
|---|-------------|--------|
| 1 | This plan (`phase25_checklist_truth.md`) | ✅ |
| 2 | Exit gate scorecard (`phase26_core_mvp_exit_gate.md`) | ✅ |
| 3 | `docs/PROGRESS_CHECKLIST.md` aligned | ✅ this pass |
| 4 | `docs/IMPLEMENTATION_MASTER_PLAN.md` aligned | ✅ this pass |
| 5 | Optional CI lint forbidding false production-ready claims | ⬜ deferred |

---

## Exit criteria (Phase 25 process — branch)

- [x] Truth model referenced from `PROGRESS_CHECKLIST.md`  
- [x] Snapshot bands for 16–26 match IMPLEMENTED / PARTIAL vs MERGED honesty  
- [x] No false MERGED for unmerged phases  
- [x] Phase 26 scored PASS/PARTIAL/FAIL against current repo  
- [ ] Phase 25 itself MERGED only after docs land on main with a later merge cycle  

---

## Explicit non-claims

- Phase 25 **does not** make the product production-ready.  
- Phase 21–24 **PARTIAL** ≠ security/observability complete.  
- Phase 16–20 **IMPLEMENTED on branch** ≠ shipped to main.  
- No **PRODUCTION VERIFIED** until Phase 26 **PASS**.

---

## References

| Doc | Path |
|-----|------|
| Checklist | `docs/PROGRESS_CHECKLIST.md` |
| Master plan | `docs/IMPLEMENTATION_MASTER_PLAN.md` |
| Exit gate | `backend/docs/plans/phase26_core_mvp_exit_gate.md` |
| 15.5 integrity | `backend/docs/plans/phase15_5_integrity_closure.md` |
| 16–24 plans | `backend/docs/plans/phase16_*.md` … `phase24_*.md` |
| Specs | `docs/MASTER_SPEC.md`, `docs/PRODUCTION_READINESS.md` |
