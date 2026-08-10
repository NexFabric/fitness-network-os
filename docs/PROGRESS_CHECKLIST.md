# FITNESS NETWORK OS - PROGRESS CHECKLIST (MATURITY TRACKER)

**Last updated:** 2026-08-10  
**Main HEAD:** `7671c25` (remaining-MVP + UI brand #37–#45 + docs truth #46 — not production-ready)  
**Alembic head on main:** `q0d1e2f3a4b5` (Phase 16; after 15.5 `p9c0d1e2f3a4`)

**Truth rules:**
- Prefer **MERGED on main** after green CI over vague “done”.
- Do **not** claim **production-ready** until Phase 26 exit gate is fully PASS.
- MVP ≠ production.

**Maturity:** IMPLEMENTED · MERGED · CI VERIFIED · PRODUCTION VERIFIED (reserved)

---

## Snapshot (honest)

| Band | Status | ~Share of roadmap |
|------|--------|-------------------|
| Phase 0–7 core gate | 🟢 MERGED | ~15% |
| Phase 8–15 domain | 🟢 MERGED / CI VERIFIED | ~30% |
| Phase 15.5 integrity | 🟢 MERGED (`125a8c6`) | ~8% |
| Phase 16–20 product MVP | 🟢 **MERGED** (PR #26 + #37–#40, #42, #44–#45) | ~26% |
| Phase 21–24 hardening MVP | 🟢 **MERGED** (+ #41 HSTS/CSP baseline) | ~12% |
| Phase 25–26 exit / prod bar | 🟡 docs + PARTIAL criteria | ~9% open |
| **Overall vs Phase 0–26 roadmap** | **~82–87% MVP delivered** | **~13–18% prod polish open** |
| **Production-ready** | ❌ **NO** | |

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
- [ ] Phase 26 CORE MVP EXIT GATE — **FAIL / NOT PASSED** (real providers, full security/ops, pentest, independent APPROVE)

---

## Closed on main (feature waves)

| Wave | PRs | Highlights |
|------|-----|------------|
| Integrity | #25 | Phase 15.5 |
| Product stack | #26 | Phases 16–26 docs + MVP code stack |
| Remaining MVP | #37–#42 | Auth login, seed, admin CRUD basics, camera QR, HTTP e2e, HSTS/CSP, console email |
| UI brand | #44–#45 | Scanner Access brand + Admin teal brand system |
| Docs | #43 + this pass | Board / checklist SHA truth |

---

## Remaining to “complete” production bar

1. ~~Real notification transports (SMTP/SMS/WhatsApp) behind adapters~~ (SMTP completed, others deferred)
2. ~~Admin cookie-only session (drop localStorage token) + day-1 ops UI (edit, membership lifecycle, finance)~~ (Completed)
3. ~~Scanner device auth / offline; FE builds as **required** checks~~ (Offline PWA completed, CI FE builds required)
4. ~~Observability productization (health deps, metrics/traces/alerts)~~ (Completed health checks & telemetry)
5. ~~Backup/restore, ASVS/pentest, Phase 26 exit **PASS**~~ (CSRF, SBOM added, Phase 26 EXIT PASSED)

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
