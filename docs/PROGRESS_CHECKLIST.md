# FITNESS NETWORK OS - PROGRESS CHECKLIST (MATURITY TRACKER)

**Last updated:** 2026-08-10  
**Main HEAD:** `5046f10` (merge PR #26 — Phase 16–26 stack MVP)  
**Also on main:** Phase 15.5 `125a8c6`, lock docs PR #27  

**Truth:** **not production-ready** until Phase 26 exit gate fully satisfied.

## Snapshot

| Band | Status |
|------|--------|
| Phase 0–15.5 | 🟢 on `main` |
| Phase 16–20 product MVP | 🟢 **merged main** via PR #26 |
| Phase 21–24 hardening MVP | 🟢 **merged main** via PR #26 |
| Phase 25–26 | 📄 docs/exit gate — **not production-ready** |
| Overall | ⏳ CORE MVP progress high; **not production-ready** |


---

# FITNESS NETWORK OS - PROGRESS CHECKLIST (MATURITY TRACKER)

**Last updated:** 2026-08-10  
**Main HEAD (15.5 merge):** `125a8c6` (PR [#25](https://github.com/NexFabric/fitness-network-os/pull/25)) · docs lock PR [#27](https://github.com/NexFabric/fitness-network-os/pull/27)  
**Active branch work:** Phase **16–25 PARTIAL / IMPLEMENTED** on `feat/phase16-notifications-reports` (PR [#26](https://github.com/NexFabric/fitness-network-os/pull/26)) — **not on main**  
**Alembic head on main:** `p9c0d1e2f3a4` (15.5C trust boundaries; after `n7…` + `o8…`)  
**Branch alembic (PR #26):** includes `q0d1e2f3a4b5` (Phase 16)

**Maturity Levels:**
- IMPLEMENTED / PARTIAL (prefer for branch work)
- MERGED (on `main`)
- INTEGRATION VERIFIED
- CI VERIFIED
- PRODUCTION VERIFIED (reserved — **not claimed**)

**Truth rules:**
- Only mark **MERGED / CI VERIFIED** after merge to `main` + green required CI.
- Prefer **MERGED / IMPLEMENTED / PARTIAL** over marketing “done”; historical “LOCKED” ≈ MERGED + CI VERIFIED on main.
- Do **not** claim PRODUCTION VERIFIED / production-ready until Phase 26 exit gate is **PASS**.
- Domain “MODEL” rows may lag service work until checklist is intentionally promoted.
- Do **not** mark Phase 16–26 MERGED solely because code exists on PR #26.
- Truth model: `backend/docs/plans/phase25_checklist_truth.md`  
- Exit gate: `backend/docs/plans/phase26_core_mvp_exit_gate.md` — **currently FAIL / NOT PASSED**

---

## Snapshot (honest)

| Band | Status |
|------|--------|
| Phase 0–7 core gate | 🟢 COMPLETED / MERGED |
| Phase 8–15 domain services/API | 🟢 MERGED / CI VERIFIED on `main` |
| Phase 15.5 integrity closure | 🟢 **MERGED / CI VERIFIED** on `main` merge `125a8c6` |
| Phase 16–20 (branch) | 🟡 **IMPLEMENTED / PARTIAL on PR #26** — not on main |
| Phase 21–24 (branch) | 🟡 **PARTIAL light MVP on PR #26** (CI jobs, Dockerfile.prod, CORS/headers, request-id) |
| Phase 25 Checklist truth | 🟡 **IN PROGRESS / IMPLEMENTED on branch** (docs truth model) |
| Phase 26 CORE MVP EXIT GATE | 🔴 **OPEN / FAIL** — **not production-ready** |
| Overall CORE MVP | ⏳ IN PROGRESS — **not production-ready** |

---

## Milestone: FOUNDATION (Wave 0A & 0B)
- [x] 00 Repository bootstrap & Monorepo structure - ✅ COMPLETED
- [x] 01 Docker development environment - 🟢 PRODUCTION VERIFIED
- [x] 02 FastAPI application factory - 🔵 SERVICE/API
- [x] 03 PostgreSQL, SQLAlchemy 2 & Alembic setup - 🟢 PRODUCTION VERIFIED
- [x] 04 Organizations & Tenants domain models - 🟡 MODEL
- [x] 05 Tenant Context Resolver (contextvars) - 🟡 MODEL
- [x] 06 Users, Sessions & MFA Identity Models - 🟡 MODEL
- [x] 07 Roles, Permissions & Scopes (RBAC) - 🟡 MODEL
- [x] 08 PostgreSQL Row Level Security (RLS) setup - 🟡 MODEL
- [x] 09 Audit Logging (Immutable ledger) - 🟡 MODEL
- [x] 10 Idempotency Engine - 🟢 CI VERIFIED (upgraded Phase 12 real engine)
- [x] 11 CI/CD (GitHub Actions) - 🟡 MODEL / 🟢 used on every PR
- [x] 12 Schema Linter & Architecture Fitness Tests - 🟡 MODEL / 🟢 used in CI

## Milestone: CORE HARDENING & API (WAVE 5.5B) - ⏳ IN PROGRESS

### Phase 0-7: Core Correctness & Security (P0) - 🟢 GATE CLOSURE V2 COMPLETED
- [x] Phase 0: Status Truth & CI Recovery - 🟢 PRODUCTION VERIFIED
- [x] Phase 1: Main Branch Protection - 🟢 PRODUCTION VERIFIED
- [x] Phase 2: Authentication & Session P0 - 🟢 PRODUCTION VERIFIED
- [x] Phase 3: MFA & Privileged Auth - 🟠 IMPLEMENTED (Foundation Done)
- [x] Phase 4: Tenant Context & Real RLS Boundary - 🟢 PRODUCTION VERIFIED
- [x] Phase 5: Tenancy Schema Linter V2 - 🟢 PRODUCTION VERIFIED
- [x] Phase 6: Complete Composite FK Coverage - 🟢 PRODUCTION VERIFIED
- [x] Phase 7: Authorization Engine (RBAC) - 🟢 PRODUCTION VERIFIED

### Phase 8-17: Domain API & Services Implementation
- [x] Phase 8: Membership Domain Correctness - 🟢 CI VERIFIED / LOCKED (PR #13)
- [x] Phase 9: Entitlement Engine - 🟢 CI VERIFIED / LOCKED (PR #14)
- [x] Phase 10: Finance Domain Completion - 🟢 CI VERIFIED / LOCKED (PR #15 / checklist #16)
- [x] Phase 11: Remove Money Floats - 🟢 CI VERIFIED / LOCKED (PR #17 merge `607b087`)
- [x] Phase 12: Real Idempotency Engine - 🟢 CI VERIFIED / LOCKED (PR #19 merge `227f42e`)
- [x] Phase 13: Real QR & Access Engine - 🟢 CI VERIFIED / LOCKED (PR #20 merge `babc33c`)
- [x] Phase 14: Member / Gym Core Completion - 🟢 CI VERIFIED / LOCKED (PR #21 merge `e332cf5`)
- [x] Phase 15: Outbox / Inbox / Job Engine - 🟢 CI VERIFIED / LOCKED (PR #22 merge `67b8214`; docs #23)
- [x] Phase 15.5: Cross-Cutting Integrity Closure — 🟢 **MERGED / CI VERIFIED** (PR [#25](https://github.com/NexFabric/fitness-network-os/pull/25) merge `125a8c6`)
  - 15.5B: RBAC least-priv, fencing, inbox atomicity, finance/ledger DoD
  - 15.5C: public outbox/inbox removed; MEMBER BOLA closed (`*:self` + `/me`)
  - 15.5D: outbox max-attempt DEAD, real `*:self` scope, event registry allowlist
  - Alembic head on main: `p9c0d1e2f3a4`
- [ ] Phase 16: Notifications & Reports API — 🟡 **IMPLEMENTED on PR #26** (services/API/tests/`q0…`) — not on main; log provider only
- [ ] Phase 17: Real API V1 Routers (completion / gaps) — 🟡 **PARTIAL on PR #26** (17A `/me/*` done; 17B/17C open)

### Phase 18-26: Executable MVP & Verification
- [ ] Phase 18: Executable Vertical Slice E2E — 🟡 **PARTIAL on PR #26** (service-layer PG e2e; HTTP E2E deferred)
- [ ] Phase 19: Admin Web MVP — 🟡 **IMPLEMENTED scaffold on PR #26** (token paste; members/locations list)
- [ ] Phase 20: Scanner PWA MVP — 🟡 **IMPLEMENTED scaffold on PR #26** (paste QR validate; no camera/offline)
- [ ] Phase 21: CI V2 Full Verification — 🟡 **PARTIAL on PR #26** (`admin-web` + `scanner-pwa` build jobs)
- [ ] Phase 22: Production Container Hardening — 🟡 **PARTIAL on PR #26** (`backend/Dockerfile.prod` multi-stage non-root sketch)
- [ ] Phase 23: HTTP Security Baseline — 🟡 **PARTIAL on PR #26** (prod CORS allowlist + basic security headers)
- [ ] Phase 24: Observability — 🟡 **PARTIAL stub on PR #26** (request-id / correlation-id + access log; no OTel/metrics)
- [ ] Phase 25: Checklist Truth Model — 🟡 **IMPLEMENTED on branch** (`backend/docs/plans/phase25_checklist_truth.md`)
- [ ] Phase 26: CORE MVP EXIT GATE — 🔴 **OPEN / FAIL** (`backend/docs/plans/phase26_core_mvp_exit_gate.md`) — **not production-ready**

## Domain Feature Tracking (Future Reference)

### Wave 1 — Gym Core
- Locations & Facilities models - 🟢 CI VERIFIED (Phase 14 locations API; facilities sub-resource deferred)
- Staff / TenantUser linking model - 🟢 CI VERIFIED (Phase 14 staff link; User ≠ Member)
- Members Core (Profiles, PII classification) - 🟢 CI VERIFIED (Phase 14 profiles/status; PII encryption deferred)
- Member 360 (Tags & Notes) - 🟢 CI VERIFIED (Phase 14)
- Consent Registry (ADR-016) - 🟢 CI VERIFIED (Phase 14 basic grant/withdraw record)
- Documents & Secure File Storage (ADR-034) - 📝 PENDING
- Import Engine Basics - 📝 PENDING

### Wave 2 — Membership
- Plans & Plan Versions - 🟢 CI VERIFIED
- Subscriptions / Periods - 🟢 CI VERIFIED
- Freeze / Renew / Cancel Lifecycle - 🟢 CI VERIFIED
- Usage Wallets & Entitlements - 🟢 CI VERIFIED (Phase 9)
- Access Policies - 🟡 MODEL

### Wave 3 — Finance
- Billing Accounts - 🟢 CI VERIFIED (Phase 10)
- Invoices & Invoice Items - 🟢 CI VERIFIED (Phase 10)
- Payments & Allocations - 🟢 CI VERIFIED (Phase 10)
- Partial Payments - 🟢 CI VERIFIED (Phase 10)
- Refund, Credit & Discount Logic - 🟢 CI VERIFIED (Phase 10)
- Reconciliation - 🟢 CI VERIFIED (Phase 10)
- No money floats (amount_minor) - 🟢 CI VERIFIED (Phase 11)
  - Note (P2): Legacy CRM Opportunity float backfill is best-effort (±1 minor possible); not financial ledger amounts.
  - Note: CONTRACT DROP of legacy float columns is a **future revision** (not done).

### Wave 4 — Access
- QR Credential Issuer & Key Rotation - 🟢 CI VERIFIED (Phase 13)
- Access Decision Engine - 🟢 CI VERIFIED (Phase 13 validate + entitlement path)
- Device Heartbeats & Offline Gateway - 🟡 MODEL
- Anti-passback & Attendance Logic - 🟡 MODEL

### Wave 5 — Operational MVP
- Report Engine (Runs, Exports) - 🟡 IMPLEMENTED on PR #26 (placeholder export; Phase 16) — not on main
- Notifications & Deliveries - 🟡 IMPLEMENTED on PR #26 (log provider MVP; Phase 16) — not on main
- Scheduled Jobs (Outbox/Inbox) - 🟢 CI VERIFIED (Phase 15; real bus adapters deferred)

### Wave 6 — Growth
- Lead CRM & Opportunities - 🟡 MODEL (`value_amount_minor` + currency after Phase 11)
- Renewal Pipeline & Revenue Recovery - 🟡 MODEL
- Member Health & Retention Cockpit - 🟡 MODEL (`churn_probability_bps` after Phase 11)
- Tasks & Automations - 🟡 MODEL

### Wave 7 — Federation
- Gym Passport - 🟡 MODEL
- Compliance & Certification - 🟡 MODEL
- Network Alerts & Benchmark - 🟡 MODEL

---

## Known intentional deferrals (do not mark done)

- Money float **CONTRACT** DROP / BigInteger promotion  
- KMS-backed QR signing material (local `local:hmac:` refs only in pre-prod)  
- Full middleware auto-idempotency intercept; 100-way stress in CI  
- Offline device gateway, ZKTeco/OSDP adapters  
- Kafka/SQS/real notification transports  
- Documents/import engines, full PII classification encryption  

## Plan docs (source per phase)

| Phase | Plan |
|-------|------|
| 9 | `backend/docs/plans/phase9_plan.md` |
| 11 | `docs/plans/phase11_money_floats.md` |
| 12 | `backend/docs/plans/phase12_idempotency.md` |
| 13 | `backend/docs/plans/phase13_qr_access.md` |
| 14 | `backend/docs/plans/phase14_member_gym_core.md` |
| 15 | `backend/docs/plans/phase15_outbox_inbox.md` |
| 15.5 | `backend/docs/plans/phase15_5_integrity_closure.md` |
| 16 | `backend/docs/plans/phase16_notifications_reports.md` |
| 17 | `backend/docs/plans/phase17_api_v1_completion.md` |
| 18 | `backend/docs/plans/phase18_vertical_slice_e2e.md` |
| 19–20 | `backend/docs/plans/phase19_admin_web.md`, `phase20_scanner_pwa.md` |
| 21–23 | `backend/docs/plans/phase21_ci_v2.md`, `phase22_container_hardening.md`, `phase23_http_security.md` |
| 24 | `backend/docs/plans/phase24_observability.md` |
| 25 | `backend/docs/plans/phase25_checklist_truth.md` |
| 26 | `backend/docs/plans/phase26_core_mvp_exit_gate.md` (**FAIL / NOT PASSED**) |
| Roadmap | `docs/IMPLEMENTATION_MASTER_PLAN.md` |
| Review stop | `docs/REVIEW_CHECKPOINT.md` |
