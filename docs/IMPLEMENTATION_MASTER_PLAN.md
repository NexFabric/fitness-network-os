# FITNESS NETWORK OS — IMPLEMENTATION MASTER PLAN

**Status:** Living roadmap (Phase 0–26)  
**Last updated:** 2026-08-10  
**Main HEAD:** `f59f1f7` (Phase 15.5 LOCKED docs) · code `125a8c6`  
**Alembic head on main:** `p9c0d1e2f3a4`  
**Active stack:** PR [#26](https://github.com/NexFabric/fitness-network-os/pull/26) Phase 16–26 open — **not LOCKED**

**Hierarchy (agents must follow):**

```text
MASTER_SPEC
  → PRODUCTION_READINESS
    → IMPLEMENTATION_MASTER_PLAN  (this file)
      → PROGRESS_CHECKLIST
        → active phase plan (docs/plans/phaseN_*.md or backend/docs/plans/)
```

Do **not** infer progress from obsolete foundation-only notes. Use `docs/PROGRESS_CHECKLIST.md` for maturity.

**Next formal step:** Review/merge Phase **16+** stack (PR #26) when CI green → continue Phase **21–26** locks individually.  
**Do not claim production-ready** until Phase 26 CORE MVP EXIT GATE is **explicitly passed**.

---

## Milestone map

| Phases | Theme | Status (see checklist) |
|--------|--------|-------------------------|
| 0–7 | Core gate / security / RLS / RBAC | 🟢 COMPLETED (gate closure) |
| 8–15 | Domain services | 🟢 CI VERIFIED / LOCKED on main |
| 15.5 | Cross-cutting integrity closure | 🟢 **CI VERIFIED / LOCKED** (`125a8c6`) |
| 16 | Notifications & reports API | 🟡 branch (PR #26) — not LOCKED |
| 17 | Real API V1 routers completion | 🟡 branch — not LOCKED |
| 18 | Vertical slice E2E | 🟡 branch — not LOCKED |
| 19–20 | Admin Web / Scanner PWA MVP | 🟡 branch — not LOCKED |
| 21–24 | CI V2, containers, HTTP security, observability | 🟠 started on branch — not LOCKED |
| 25–26 | Checklist truth + CORE MVP EXIT GATE | ⬜ criteria; **26 NOT PASSED** |

---

## Locked phase notes (summary)

### Phase 11–15 — LOCKED

See prior lock notes in git history and per-phase plans under `backend/docs/plans/` / `docs/plans/`.

### Phase 15.5 — LOCKED (main `125a8c6`)

- PR #25 merge `125a8c6` · lock docs PR #27 · alembic head `p9c0d1e2f3a4`
- No public generic `/outbox` HTTP inject; MEMBER BOLA closed; event registry; outbox max-attempts → DEAD
- Details: `backend/docs/plans/phase15_5_integrity_closure.md`

### Phase 16–20 — ACTIVE ON BRANCH (not LOCKED)

- Notifications/reports domain + API, self-service `/me`, vertical slice E2E, admin-web, scanner-pwa
- Prefer Outbox for async delivery; domain → Event → Notification (no WhatsApp shortcuts)
- **Do not mark LOCKED** until merge to main + green required CI

### Phase 21–26 — hardening open (not LOCKED)

| Phase | Plan | Branch status |
|-------|------|---------------|
| 21 | `phase21_ci_v2.md` | FE Admin Web + Scanner PWA build jobs |
| 22 | `phase22_container_hardening.md` | `Dockerfile.prod` multi-stage non-root |
| 23 | `phase23_http_security.md` | ENVIRONMENT + CORS_ORIGINS + security headers |
| 24 | `phase24_observability.md` | request-id + structured access log stub |
| 25 | `phase25_checklist_truth.md` | maturity truth model |
| 26 | `phase26_core_mvp_exit_gate.md` | exit criteria — **NOT PASSED** |

---

## Non-negotiables

- Gym = tenant; RLS FORCE on tenant tables  
- Money: `amount_minor` int (never binary float)  
- Expand → backfill → switch → contract for destructive schema  
- Domain boundaries (no Membership → WhatsApp shortcuts)  
- Transactional outbox + idempotency on money/entitlement mutations  
- No public generic outbox/inbox HTTP reintroduction  

## Foundation archive (COMPLETED)

Repository bootstrap, Docker, FastAPI factory, SQLAlchemy/Alembic, org/tenant, auth/MFA foundation, RLS helpers, RBAC matrix, audit model, CI gates — complete under Phase 0–7. Historical detail remains in git history and older docs; do not treat foundation section as the active execution plan.
