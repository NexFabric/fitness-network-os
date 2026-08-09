# Phase 25 — Checklist Truth Model

**Status:** 🟠 **IMPLEMENTED on branch** (process + checklist sync) — **not LOCKED**  
**Plan path:** `backend/docs/plans/phase25_checklist_truth.md`  
**Source of maturity truth:** `docs/PROGRESS_CHECKLIST.md`  
**Do not claim:** production-ready (Phase 26 exit gate only — **NOT PASSED**)

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

---

## Maturity levels (canonical)

| Badge | Meaning | Allowed only when |
|-------|---------|-------------------|
| 📝 PENDING | Not started | Default for future work |
| ⬜ STARTING / skeleton / stub | Plan or thin spike only | Plan doc and/or minimal code; **no** merge claim |
| 🟡 MODEL | Schema / model present; service incomplete | Models + migrations may exist; product surface incomplete |
| 🟠 **IMPLEMENTED on branch** / **IMPLEMENTED on main** | Code present | Feature exists in tree; tests may be partial; **prefer this wording over LOCK ritual** |
| 🔵 SERVICE/API | Service + HTTP surface exist | Not yet full CI lock narrative |
| 🟢 CI VERIFIED | Required CI green for that change | PR merged **or** equivalent main-required checks green |
| 🟢 CI VERIFIED / **LOCKED** | Phase closed on `main` | **Merge to `main` + green required CI** + checklist updated with PR/merge SHA |
| 🟢 PRODUCTION VERIFIED | Live/prod-grade acceptance | Explicitly rare; **never** before Phase 26 exit gate **PASS** |

---

## Hard truth rules

1. **LOCKED requires main.** Feature-branch “done” is at most 🟠 **IMPLEMENTED on branch**. Never write **LOCKED** for unmerged phases.
2. **CI VERIFIED is evidence-based.** Point to PR number and/or merge SHA when promoting.
3. **No production-ready claim** until Phase **26** exit gate is **PASS** with evidence (currently **NOT PASSED**).
4. **Domain rows lag services until promoted.**
5. **Plans are not locks.** Presence of `phaseN_*.md` ≠ phase complete.
6. **PROGRESS_CHECKLIST wins over chat memory.**
7. **Deferred is not done.** “Known intentional deferrals” stay open.
8. Prefer **IMPLEMENTED on main/branch** language over waiting on human lock rituals — but never upgrade to LOCKED or production-ready without evidence.

---

## Promotion recipe (phase lock)

1. Phase plan exit criteria checked with evidence.
2. PR **merged to `main`**.
3. Required main CI green.
4. Update checklist + plan header + master plan row with merge SHA.
5. **Do not** lock future phases by association.

---

## Opening honesty — stack status (2026-08-10)

| Phase | Honest status | Notes |
|-------|---------------|--------|
| 0–15.5 | 🟢 CI VERIFIED / LOCKED on `main` | Merge `125a8c6` (15.5) |
| 16–20 | 🟠 **IMPLEMENTED on branch** | PR #26 — not LOCKED until merge + CI |
| 21 CI V2 | 🟠 **IMPLEMENTED on branch** | admin-web + scanner-pwa jobs in `ci.yml` |
| 22 Container | 🟠 **IMPLEMENTED on branch** | `Dockerfile.prod` multi-stage non-root |
| 23 HTTP security | 🟠 **IMPLEMENTED on branch** | CORS env + security headers |
| 24 Observability | 🟠 **IMPLEMENTED on branch** | Request id + structured access log |
| 25 Checklist truth | 🟠 **IMPLEMENTED on branch** | This doc + checklist language |
| 26 Exit gate | 📄 **CRITERIA EVALUATED** | **NOT PASSED** — see phase26 matrix |

---

## Anti-patterns (reject in review)

- Marking LOCKED because tests pass locally only
- Marking PRODUCTION VERIFIED because Compose runs
- False LOCKED on feature branch without main merge SHA
- Claiming Phase 26 PASS while any hard criterion is FAIL
- “Basically done” narrative instead of checklist bands

---

## Exit criteria (Phase 25 process — branch)

- [x] Truth model referenced from `PROGRESS_CHECKLIST.md`
- [x] Snapshot bands for 16–26 match **IMPLEMENTED on branch** vs LOCKED honesty
- [x] No false LOCKED for unmerged phases
- [ ] **CI VERIFIED / LOCKED** only after this model is used on a post-16 main merge cycle
