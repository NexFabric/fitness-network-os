# FITNESS NETWORK OS - PROGRESS CHECKLIST (MATURITY TRACKER)

**Last updated:** 2026-08-10  
**Main HEAD:** `398e858` lineage · stack merge `5046f10` (PR [#26](https://github.com/NexFabric/fitness-network-os/pull/26))  
**15.5:** `125a8c6` (PR [#25](https://github.com/NexFabric/fitness-network-os/pull/25)) · docs PR [#27](https://github.com/NexFabric/fitness-network-os/pull/27)  
**Alembic head on main:** `q0d1e2f3a4b5` (Phase 16)

**Maturity Levels:** IMPLEMENTED · MERGED · CI VERIFIED · PRODUCTION VERIFIED (reserved)

**Truth rules:**
- Prefer **IMPLEMENTED on main** for completed MVP code; historical LOCKED ≈ MERGED + CI VERIFIED.
- Do **not** claim PRODUCTION VERIFIED / production-ready until Phase 26 exit gate is **PASS**.
- Truth model: `backend/docs/plans/phase25_checklist_truth.md`
- Exit gate: `backend/docs/plans/phase26_core_mvp_exit_gate.md` — **currently FAIL / NOT PASSED**

---

## Snapshot (honest)

| Band | Status |
|------|--------|
| Phase 0–7 core gate | 🟢 COMPLETED / MERGED |
| Phase 8–15 domain | 🟢 MERGED / CI VERIFIED |
| Phase 15.5 integrity | 🟢 MERGED / CI VERIFIED (`125a8c6`) |
| Phase 16–20 product MVP | 🟠 **IMPLEMENTED on main** (`5046f10`) — PARTIAL depth |
| Phase 21–25 hardening / truth | 🟠 **IMPLEMENTED on main** — MVP / PARTIAL |
| Phase 26 exit gate | 🔴 **FAIL / NOT PASSED** |
| Overall CORE MVP | ⏳ high progress — **not production-ready** |

---

## Phase 0–15.5 (on main)

- [x] Phase 0–7 core correctness & security — COMPLETED  
- [x] Phase 8–15 domain services — MERGED / CI VERIFIED (PRs #13–#22)  
- [x] Phase 15.5 integrity closure — MERGED `125a8c6` (PR #25)  
  - Public outbox/inbox removed; MEMBER `*:self`; event registry; outbox max-attempts DEAD  

## Phase 16–26 (MVP on main via PR #26)

- [x] Phase 16: Notifications & Reports — 🟠 IMPLEMENTED on main (log provider only)  
- [x] Phase 17: API V1 completion — 🟠 IMPLEMENTED on main (17A `/me/*`; 17B/17C gaps)  
- [x] Phase 18: Vertical slice E2E — 🟠 IMPLEMENTED on main (service-layer PG; HTTP deferred)  
- [x] Phase 19: Admin Web MVP — 🟠 IMPLEMENTED on main (scaffold)  
- [x] Phase 20: Scanner PWA MVP — 🟠 IMPLEMENTED on main (scaffold)  
- [x] Phase 21: CI V2 — 🟠 IMPLEMENTED on main (admin-web + scanner-pwa build jobs)  
- [x] Phase 22: Container hardening — 🟠 IMPLEMENTED on main (`Dockerfile.prod`)  
- [x] Phase 23: HTTP security — 🟠 IMPLEMENTED on main (prod CORS + headers)  
- [x] Phase 24: Observability — 🟠 IMPLEMENTED on main (X-Request-ID + access log)  
- [x] Phase 25: Checklist truth model — 🟠 IMPLEMENTED on main (docs)  
- [ ] Phase 26: CORE MVP EXIT GATE — 🔴 **FAIL / NOT PASSED** — **not production-ready**

## Domain feature notes

- Wave 1–4 core (member/membership/finance/access) — 🟢 on main  
- Wave 5 notifications/reports — 🟠 IMPLEMENTED on main (MVP)  
- Real notification transports, camera scanner, offline gateway — deferred  

## Known intentional deferrals

- Money float CONTRACT DROP  
- KMS-backed QR signing  
- Full middleware auto-idempotency / 100-way stress  
- Offline device gateway / hardware adapters  
- Kafka/SQS/real notification transports  
- Documents/import; full PII encryption  
- Backup/restore operational drill  
- OpenTelemetry / business metrics productization  

## Plan docs

| Phase | Path |
|-------|------|
| 15.5 | `backend/docs/plans/phase15_5_integrity_closure.md` |
| 16–20 | `backend/docs/plans/phase16_*.md` … `phase20_*.md` |
| 21–26 | `backend/docs/plans/phase21_ci_v2.md` … `phase26_core_mvp_exit_gate.md` |
| Health | `backend/docs/plans/CONTROL_HEALTH_REPORT.md` |
| Roadmap | `docs/IMPLEMENTATION_MASTER_PLAN.md` |
