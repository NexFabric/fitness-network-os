# FITNESS NETWORK OS — IMPLEMENTATION MASTER PLAN

**Status:** Living roadmap (Phase 0–26)  
**Last updated:** 2026-08-10  
**Main HEAD:** `398e858`  
**Alembic head:** `q0d1e2f3a4b5`  

**Hierarchy:** MASTER_SPEC → PRODUCTION_READINESS → this plan → PROGRESS_CHECKLIST → phase plans  

**Do not claim production-ready** until Phase 26 exit gate is **PASS**.

---

## Milestone map (synced to main)

| Phases | Theme | Status on main |
|--------|--------|----------------|
| 0–7 | Core gate | 🟢 MERGED |
| 8–15 | Domain services | 🟢 MERGED |
| 15.5 | Integrity closure | 🟢 MERGED `125a8c6` |
| 16 | Notifications & reports | 🟢 MERGED (PR #26) |
| 17 | `/me` + API V1 partial | 🟢 MERGED (17A); 17B/C gaps |
| 18 | Vertical E2E | 🟢 MERGED (service e2e) |
| 19–20 | Admin Web / Scanner PWA | 🟢 MERGED scaffold MVP |
| 21 | CI V2 frontend jobs | 🟢 MERGED |
| 22–24 | Container / HTTP / request-id | 🟢 MERGED MVP |
| 25 | Checklist truth | 🟢 docs MERGED |
| 26 | CORE MVP EXIT GATE | 🔴 **NOT PASSED** |

**Roadmap completion (MVP vs full prod):** ~**75–80%** of phase surface area delivered as MVP on main; ~**20–25%** production bar remaining.

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
