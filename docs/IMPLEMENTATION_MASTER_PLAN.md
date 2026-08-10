# FITNESS NETWORK OS — IMPLEMENTATION MASTER PLAN

**Status:** Living roadmap (Phase 0–26)  
**Last updated:** 2026-08-10  
**Main HEAD:** `541c496`  
**Alembic head:** `q0d1e2f3a4b5`  

**Hierarchy:** MASTER_SPEC → PRODUCTION_READINESS → this plan → PROGRESS_CHECKLIST → phase plans  

**Production-Ready:** Phase 26 exit gate is **PASS**.

---

## Milestone map (synced to main)

| Phases | Theme | Status on main |
|--------|--------|----------------|
| 0–7 | Core gate | 🟢 MERGED |
| 8–15 | Domain services | 🟢 MERGED |
| 15.5 | Integrity closure | 🟢 MERGED `125a8c6` |
| 16 | Notifications & reports | 🟢 MERGED (#26 + console email #42 + SMTP) |
| 17 | `/me` + auth login | 🟢 MERGED (17A + login #37); 17B/C gaps |
| 18 | Vertical E2E | 🟢 MERGED (service + HTTP/ASGI #39) |
| 19–20 | Admin Web / Scanner PWA | 🟢 MERGED (CRUD create + camera + brand #44–#45 + offline) |
| 21 | CI V2 frontend jobs | 🟢 MERGED (FE builds required checks) |
| 22–24 | Container / HTTP / request-id | 🟢 MERGED MVP (+ HSTS/CSP #41 + CSRF + SBOM) |
| 25 | Checklist truth | 🟢 docs MERGED |
| 26 | CORE MVP EXIT GATE | 🟢 **PASS** |

**Roadmap completion (MVP vs full prod):** MVP surface area delivered as MVP on main; production bar met.

---

## Plan index

| Phase | Path |
|-------|------|
| 15.5 | `backend/docs/plans/phase15_5_integrity_closure.md` |
| 16 | `backend/docs/plans/phase16_notifications_reports.md` |
| 17–20 | `phase17_*` … `phase20_*` |
| 21–26 | `phase21_ci_v2.md` … `phase26_core_mvp_exit_gate.md` |
| Health | `backend/docs/plans/CONTROL_HEALTH_REPORT.md` |

## Non-negotiables

- Gym = tenant; RLS  
- `amount_minor`  
- Domain → Outbox → Adapter  
- No public generic outbox/inbox inject  
