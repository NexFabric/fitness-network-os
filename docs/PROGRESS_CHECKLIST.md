# FITNESS NETWORK OS - PROGRESS CHECKLIST (MATURITY TRACKER)

**Maturity Levels:**
- IMPLEMENTED
- INTEGRATION VERIFIED
- CI VERIFIED
- PRODUCTION VERIFIED

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
- [x] 10 Idempotency Engine - 🟡 MODEL
- [x] 11 CI/CD (GitHub Actions) - 🟡 MODEL
- [x] 12 Schema Linter & Architecture Fitness Tests - 🟡 MODEL

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
- [x] Phase 8: Membership Domain Correctness - 🟢 CI VERIFIED
- [x] Phase 9: Entitlement Engine - 🟢 CI VERIFIED
- [x] Phase 10: Finance Domain Completion - 🟢 CI VERIFIED
- [x] Phase 11: Remove Money Floats - 🟢 CI VERIFIED / LOCKED (PR #17 merge `607b087`)
- [x] Phase 12: Real Idempotency Engine - 🟢 CI VERIFIED / LOCKED (PR #19 merge `227f42e`)
- [x] Phase 13: Real QR & Access Engine - 🟢 CI VERIFIED / LOCKED (PR #20 merge `babc33c`)
- [x] Phase 14: Member / Gym Core Completion - 🟢 CI VERIFIED / LOCKED (PR #21 merge `e332cf5`)
- [x] Phase 15: Outbox / Inbox / Job Engine - 🟢 CI VERIFIED / LOCKED (PR #22 merge `67b8214`)
- [ ] Phase 16: Notifications & Reports API
- [ ] Phase 17: Real API V1 Routers

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
- Locations & Facilities models - 🟠 SERVICE (Phase 14; facilities sub-resource deferred)
- Staff / TenantUser linking model - 🟠 SERVICE (Phase 14)
- Members Core (Profiles, PII classification) - 🟠 SERVICE (Phase 14; PII encryption deferred)
- Member 360 (Tags & Notes) - 🟠 SERVICE (Phase 14)
- Consent Registry (ADR-016) - 🟠 SERVICE (Phase 14 basic record)
- Documents & Secure File Storage (ADR-034) - 📝 PENDING
- Import Engine Basics - 📝 PENDING

### Wave 2 — Membership
- Plans & Plan Versions - 🟢 CI VERIFIED
- Subscriptions / Periods - 🟢 CI VERIFIED
- Freeze / Renew / Cancel Lifecycle - 🟢 CI VERIFIED
- Usage Wallets & Entitlements - 🟢 SERVICE (Phase 9)
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

### Wave 4 — Access
- QR Credential Issuer & Key Rotation - 🟢 CI VERIFIED (Phase 13)
- Access Decision Engine - 🟢 SERVICE (Phase 13 validate path)

- Device Heartbeats & Offline Gateway - 🟡 MODEL
- Anti-passback & Attendance Logic - 🟡 MODEL

### Wave 5 — Operational MVP
- Report Engine (Runs, Exports) - 🟡 MODEL
- Notifications & Deliveries - 🟡 MODEL
- Scheduled Jobs (Outbox/Inbox) - 🟢 CI VERIFIED (Phase 15)

### Wave 6 — Growth
- Lead CRM & Opportunities - 🟡 MODEL (`value_amount_minor` + currency after Phase 11)
- Renewal Pipeline & Revenue Recovery - 🟡 MODEL
- Member Health & Retention Cockpit - 🟡 MODEL (`churn_probability_bps` after Phase 11)
- Tasks & Automations - 🟡 MODEL

### Wave 7 — Federation
- Gym Passport - 🟡 MODEL
- Compliance & Certification - 🟡 MODEL
- Network Alerts & Benchmark - 🟡 MODEL
