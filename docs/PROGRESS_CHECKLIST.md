# FITNESS NETWORK OS - PROGRESS CHECKLIST (MATURITY TRACKER)

**Last updated:** 2026-08-10  
**Main HEAD:** `e19d935` (PR #26 stack + docs #28/#30/#32; demo seed on follow-up branch)  
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
| Phase 16–20 product MVP | 🟢 **MERGED** (PR #26 → `5046f10`) | ~25% |
| Phase 21–24 hardening MVP | 🟢 **MERGED** (same stack) | ~12% |
| Phase 25–26 exit / prod bar | 🟡 docs + PARTIAL criteria | ~10% open |
| **Overall vs Phase 0–26 roadmap** | **~75–80% MVP delivered** | **~20–25% prod polish open** |
| **Production-ready** | ❌ **NO** | |

---

## Phase checklist

### Foundation & core (0–7)
- [x] Bootstrap, Docker, FastAPI, Postgres/Alembic, tenancy, auth/MFA foundation, RLS, RBAC, CI

### Domain (8–15.5) — on main
- [x] Phase 8–15 domain engines — MERGED  
- [x] Phase 15.5 integrity (no public outbox, `*:self`, event registry, outbox max-attempts) — MERGED PR #25  

### Product stack (16–20) — on main via PR #26
- [x] Phase 16 Notifications & Reports API + migration `q0…`  
- [x] Phase 17 `/me/*` self-service expansion (partial 17B/C staff gaps remain)  
- [x] Phase 18 vertical slice E2E (service-layer; full HTTP e2e still light)  
- [x] Phase 19 Admin Web MVP scaffold  
- [x] Phase 20 Scanner PWA MVP scaffold  

### Hardening (21–24) — on main (MVP depth)
- [x] Phase 21 CI V2: admin-web + scanner-pwa build jobs  
- [x] Phase 22 `Dockerfile.prod` multi-stage non-root  
- [x] Phase 23 CORS (prod env) + security headers  
- [x] Phase 24 request-id / structured access logging  

### Exit (25–26)
- [x] Phase 25 checklist truth model (docs)  
- [ ] Phase 26 CORE MVP EXIT GATE — **FAIL / NOT PASSED** (real providers, full security/ops, pentest, etc.)

---

## Remaining to “complete” production bar

1. Real notification transports (email/SMS/WhatsApp) behind adapters  
2. Full HTTP E2E + richer Admin/Scanner product  
3. HSTS/CSP/rate limit/prod CORS allowlist discipline  
4. Observability productization (metrics/traces/alerts)  
5. Backup/restore, ASVS/pentest, Phase 26 exit **PASS**  

---

## Related docs

- `docs/REVIEW_CHECKPOINT.md`  
- `docs/IMPLEMENTATION_MASTER_PLAN.md`  
- `backend/docs/plans/phase26_core_mvp_exit_gate.md`  
- `backend/docs/plans/CONTROL_HEALTH_REPORT.md`  
- `backend/docs/plans/REMAINING_WORK_BOARD.md`  
- `READY_TO_RUN.md`  
