# FITNESS NETWORK OS - PROGRESS CHECKLIST (MATURITY TRACKER)

**Maturity Levels:**
- 🟡 MODEL: Database tables and migrations exist.
- 🔵 SERVICE/API: Business logic and API endpoints exist.
- 🟢 PRODUCTION VERIFIED: Fully tested (integration/E2E), authorized, and CI-gated.
- ✅ COMPLETED: All 3 tiers achieved.

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

### Phase 0-7: Core Correctness & Security (P0) - ✅ COMPLETED
- [x] Phase 0: Status Truth & CI Recovery - 🟢 PRODUCTION VERIFIED
- [x] Phase 1: Main Branch Protection - 🟢 PRODUCTION VERIFIED
- [x] Phase 2: Authentication & Session P0 - 🟢 PRODUCTION VERIFIED
- [x] Phase 3: MFA & Privileged Auth - 🟢 PRODUCTION VERIFIED
- [x] Phase 4: Tenant Context & Real RLS Boundary - 🟢 PRODUCTION VERIFIED
- [x] Phase 5: Tenancy Schema Linter V2 - 🟢 PRODUCTION VERIFIED
- [x] Phase 6: Complete Composite FK Coverage - 🟢 PRODUCTION VERIFIED
- [x] Phase 7: Authorization Engine (RBAC) - 🟢 PRODUCTION VERIFIED

### Phase 8-17: Domain API & Services Implementation
- [ ] Phase 8: Membership Domain Correctness
- [ ] Phase 9: Entitlement Engine
- [ ] Phase 10: Finance Domain Completion
- [ ] Phase 11: Remove Money Floats
- [ ] Phase 12: Real Idempotency Engine
- [ ] Phase 13: Real QR & Access Engine
- [ ] Phase 14: Member / Gym Core Completion
- [ ] Phase 15: Outbox / Inbox / Job Engine
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
- Locations & Facilities models - 🟡 MODEL
- Staff / TenantUser linking model - 🟡 MODEL
- Members Core (Profiles, PII classification) - 🟡 MODEL
- Member 360 (Tags & Notes) - 🟡 MODEL
- Consent Registry (ADR-016) - 🟡 MODEL
- Documents & Secure File Storage (ADR-034) - 📝 PENDING
- Import Engine Basics - 📝 PENDING

### Wave 2 — Membership
- Plans & Plan Versions - 🟡 MODEL
- Subscriptions / Periods - 🟡 MODEL
- Freeze / Renew / Cancel Lifecycle - 🟡 MODEL
- Usage Wallets & Entitlements - 🟡 MODEL
- Access Policies - 🟡 MODEL

### Wave 3 — Finance
- Billing Accounts - 🟡 MODEL
- Invoices & Invoice Items - 🟡 MODEL
- Payments & Allocations - 🟡 MODEL
- Partial Payments - 🟡 MODEL
- Refund, Credit & Discount Logic - 📝 PENDING
- Reconciliation - 📝 PENDING

### Wave 4 — Access
- QR Credential Issuer & Key Rotation - 🟡 MODEL
- Access Decision Engine - 🟡 MODEL
- Device Heartbeats & Offline Gateway - 🟡 MODEL
- Anti-passback & Attendance Logic - 🟡 MODEL

### Wave 5 — Operational MVP
- Report Engine (Runs, Exports) - 🟡 MODEL
- Notifications & Deliveries - 🟡 MODEL
- Scheduled Jobs (Outbox/Inbox) - 🟡 MODEL

### Wave 6 — Growth
- Lead CRM & Opportunities - 🟡 MODEL
- Renewal Pipeline & Revenue Recovery - 🟡 MODEL
- Member Health & Retention Cockpit - 🟡 MODEL
- Tasks & Automations - 🟡 MODEL

### Wave 7 — Federation
- Gym Passport - 🟡 MODEL
- Compliance & Certification - 🟡 MODEL
- Network Alerts & Benchmark - 🟡 MODEL
