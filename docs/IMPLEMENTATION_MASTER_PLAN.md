# FITNESS NETWORK OS — IMPLEMENTATION MASTER PLAN

**Status:** Living roadmap (Phase 0–27)  
**Last updated:** 2026-08-13
**Main HEAD:** `2a1002d` · **Alembic head:** `v5c6d7e8f9a0`

**Hierarchy:** MASTER_SPEC → PRODUCTION_READINESS → this plan → PROGRESS_CHECKLIST → phase plans  

**Production-Ready:** **NO** — Phase 26 NOT PASSED; active **Phase 27 Final Production Closure**.

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
| 26 | CORE MVP EXIT GATE | 🔴 **NOT PASSED** — no external pentest evidence (docs/ops/ASVS_PENTEST_STATUS.md) |
| 27 | UI production closure (RBAC portals) | 🟢 UI/RBAC wave landed — role-guarded portals, `/me/session`, trainer assignment scope, federation `/admin/*` (ADR-043), PWA icon set |
| 27.1 | Device channel hardening | 🟢 HMAC request signing + single-use nonce on the device channel (ADR-044); CodeQL high + workflow-permission alerts cleared |
| 27.2 | Operations console depth | 🟢 Devices, notifications, reports, staff, location edit, full membership lifecycle; Redis-backed login rate limit |
| 27.3 | Plan catalogue + membership creation | 🟢 `/plans` (versions, publish) + `POST /memberships` — closes API-1; delivery/run history endpoints close API-2 |
| 27.4 | Final production closure | 🟢 MERGED `2a1002d` — privileged MFA + session rotation, private S3 report storage, real Prometheus metrics, frozen non-root image, required Playwright gate; **code** closed, external evidence gates still open |

**Roadmap completion (MVP vs full prod):** MVP surface area delivered on main. The production bar is **not** met — Phase 26 is open.

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
