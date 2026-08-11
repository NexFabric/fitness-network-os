# FITNESS NETWORK OS - PROGRESS CHECKLIST (MATURITY TRACKER)

**Last updated:** 2026-08-10  
**Program:** Phase **27 — Final Production Closure** (`backend/docs/plans/PHASE_27_FINAL_PRODUCTION_CLOSURE.md`)  
**Alembic head on main:** `q0d1e2f3a4b5` (Phase 16; after 15.5 `p9c0d1e2f3a4`)

**Truth rules:**
- Prefer **MERGED on main** after green **required** CI over vague “done”.
- Do **not** claim **production-ready** until Phase 27 P0 closed + evidence gates + independent human APPROVE.
- MVP code on main ≠ production-ready. Phase 26 PASS is **NOT** currently verified.
- Required CI red → not CI VERIFIED / not LOCKED.

**Maturity:** IMPLEMENTED · MERGED · ⚠️ CI NOT GREEN (recent main) · PRODUCTION **NO-GO**

---

## Snapshot (honest)

| Band | Status | Note |
|------|--------|------|
| Phase 0–7 core gate | 🟢 MERGED | Architecture GO |
| Phase 8–15 domain | 🟢 MERGED | Tenancy/finance/outbox strong |
| Phase 15.5 integrity | 🟢 MERGED | Maintain |
| Phase 16–20 product MVP | 🟢 MERGED (depth partial) | Admin/Scanner polish open |
| Phase 21–24 hardening MVP | 🟡 MERGED code / 🔴 CI flaky | CSRF/auth still P0 |
| Phase 25–26 exit / prod bar | 🔴 **NOT PASSED** | Truth corrected |
| **Phase 27 production closure** | 🔴 **ACTIVE** | P0→P1→P2 board |
| **Production-ready** | ❌ **NO** | Public launch NO-GO |

---

## Phase checklist

### Foundation & core (0–7)
- [x] Bootstrap, Docker, FastAPI, Postgres/Alembic, tenancy, auth/MFA foundation, RLS, RBAC, CI

### Domain (8–15.5) — on main
- [x] Phase 8–15 domain engines — MERGED  
- [x] Phase 15.5 integrity (no public outbox, `*:self`, event registry, outbox max-attempts) — MERGED PR #25  

### Product stack (16–20) — on main
- [x] Phase 16 Notifications & Reports API + migration `q0…` (+ console email adapter #42)  
- [x] Phase 17 `/me/*` self-service + public `POST /api/v1/auth/login|logout` (#37); 17B/C staff/OpenAPI gaps remain  
- [x] Phase 18 vertical slice E2E — service-layer **+ HTTP/ASGI** (`test_http_vertical_slice.py` #39)  
- [x] Phase 19 Admin Web — login, create member/location, **GymClubNex brand system** (#37–#38, #45)  
- [x] Phase 20 Scanner PWA — camera QR + paste, **Access brand polish** (#40, #44)  

### Hardening (21–24) — on main (MVP depth)
- [x] Phase 21 CI V2: admin-web + scanner-pwa build jobs (not yet **required** branch checks)  
- [x] Phase 22 `Dockerfile.prod` multi-stage non-root  
- [x] Phase 23 CORS (prod env) + headers + **HSTS/CSP baseline** (#41) + light login rate limit  
- [x] Phase 24 request-id / structured access logging  

### Exit (25–26)
- [x] Phase 25 checklist truth model (docs)  
- [ ] Phase 26 CORE MVP EXIT GATE — **NOT PASSED** (superseded by Phase 27 closure; independent APPROVE + green CI required)

---

## Closed on main (feature waves)

| Wave | PRs | Highlights |
|------|-----|------------|
| Integrity | #25 | Phase 15.5 |
| Product stack | #26 | Phases 16–26 docs + MVP code stack |
| Remaining MVP | #37–#42 | Auth login, seed, admin CRUD basics, camera QR, HTTP e2e, HSTS/CSP, console email |
| UI brand | #44–#45 | Scanner Access brand + Admin teal brand system |
| Docs | #43 | Board / checklist SHA truth |
| Prod Hardening | #48 | Strict HttpOnly Cookies, Pytest Deadlock Fix, Full Mypy/Ruff compliance, Test isolation |

---

## Remaining to “complete” production bar

1. ~~Real notification transports (SMTP/SMS/WhatsApp) behind adapters~~ (SMTP completed, others deferred)
2. ~~Admin cookie-only session (drop localStorage token) + day-1 ops UI (edit, membership lifecycle, finance)~~ (Completed)
3. ~~Scanner device auth / offline~~; FE builds as **required** checks (Completed)
4. ~~Observability productization (health deps, metrics/traces/alerts)~~ (Completed `/live`, `/ready`, `/health`)
5. ~~Backup/restore script & ASVS L2 compliance report~~ (Completed)

Live backlog: `backend/docs/plans/REMAINING_WORK_BOARD.md`

---

## Related docs

- `docs/REVIEW_CHECKPOINT.md`  
- `docs/IMPLEMENTATION_MASTER_PLAN.md`  
- `backend/docs/plans/phase26_core_mvp_exit_gate.md`  
- `backend/docs/plans/CONTROL_HEALTH_REPORT.md`  
- `backend/docs/plans/REMAINING_WORK_BOARD.md`  
- `backend/docs/plans/STANDING_REVIEW_latest.md`  
- `frontend/UI_BRAND_SYSTEM.md`  
- `READY_TO_RUN.md`  
