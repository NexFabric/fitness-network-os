# FITNESS NETWORK OS - PROGRESS CHECKLIST (MATURITY TRACKER)

**Last updated:** 2026-08-10  
**Main HEAD (docs sync base):** `af8f809` (Phase 8–15 LOCKED)  
**Active branch work:** Phase **15.5** on PR [#25](https://github.com/NexFabric/fitness-network-os/pull/25) head `ffba0a8`; Phase **16** 🟠 **IN PROGRESS** on `feat/phase16-notifications-reports` (stacked; merge **after** 15.5 LOCKED)  
**Alembic head (15.5 branch):** `p9c0d1e2f3a4` (after `n7…` + `o8…`)

**Maturity Levels:**
- IMPLEMENTED
- INTEGRATION VERIFIED
- CI VERIFIED
- PRODUCTION VERIFIED

**Truth rules:**
- Only mark **CI VERIFIED / LOCKED** after merge to `main` + green required CI.
- Do **not** claim PRODUCTION VERIFIED / production-ready until Phase 26 exit gate.
- Domain “MODEL” rows may lag service work until checklist is intentionally promoted.

---

## Snapshot (honest)

| Band | Status |
|------|--------|
| Phase 0–7 core gate | 🟢 COMPLETED |
| Phase 8–15 domain services/API | 🟢 CI VERIFIED / LOCKED on `main` |
| Phase 15.5 integrity closure | 🟡 **CODE + PR CI GREEN** (`ffba0a8`) — **not LOCKED** (await human APPROVE + merge + main CI) |
| Phase 16 Notifications & Reports | 🟠 **IN PROGRESS** on `feat/phase16-notifications-reports` (merge after 15.5 LOCKED) |
| Phase 17–26 | ⬜ NOT STARTED |
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
- [ ] Phase 15.5: Cross-Cutting Integrity Closure — 🟡 **PR #25** head `ffba0a8` (15.5B/C/D applied; PR CI green; **await independent APPROVE + merge** → then LOCKED)
  - 15.5B: RBAC least-priv, fencing, inbox atomicity, finance/ledger DoD
  - 15.5C: public outbox/inbox removed; MEMBER BOLA closed (`*:self` + `/me`)
  - 15.5D: outbox max-attempt DEAD, real `*:self` scope, event registry allowlist
  - Alembic: `p9c0d1e2f3a4`
- [ ] Phase 16: Notifications & Reports API — 🟠 **IN PROGRESS** on `feat/phase16-notifications-reports` (plan: `backend/docs/plans/phase16_notifications_reports.md`; **merge only after 15.5 LOCKED on main**)
  - 16A: contracts/models + event registry + permissions
  - 16B: schedule + outbox consumer (Domain → Outbox → Notification → Adapter)
  - 16C: log provider adapters only (no real WhatsApp/SMS SDK)
  - 16D: report definitions/runs (MVP export metadata)
  - 16E: tests/CI — no generic public `/inbox`; provider webhooks later
- [ ] Phase 17: Real API V1 Routers (completion / gaps)

### Phase 18-26: Executable MVP & Verification
- [ ] Phase 18: Executable Vertical Slice E2E
- [ ] Phase 19: Admin Web MVP
- [ ] Phase 20: Scanner PWA MVP
- [ ] Phase 21: CI V2 Full Verification
- [ ] Phase 22: Production Container Hardening
- [ ] Phase 23: HTTP Security Baseline
- [ ] Phase 24: Observability
- [ ] Phase 25: Checklist Truth Model Implementation
- [ ] Phase 26: CORE MVP EXIT GATE

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
- Report Engine (Runs, Exports) - 🟡 MODEL → Phase 16
- Notifications & Deliveries - 🟡 MODEL → Phase 16
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
| Roadmap | `docs/IMPLEMENTATION_MASTER_PLAN.md` |
| Review stop | `docs/REVIEW_CHECKPOINT.md` |
