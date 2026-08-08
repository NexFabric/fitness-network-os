# FITNESS NETWORK OS - PROGRESS CHECKLIST

## Milestone: FOUNDATION (Wave 0A & 0B) - ✅ COMPLETED
- [x] 00 Repository bootstrap & Monorepo structure
- [x] 01 Docker development environment
- [x] 02 FastAPI application factory
- [x] 03 PostgreSQL, SQLAlchemy 2 & Alembic setup
- [x] 04 Organizations & Tenants domain models
- [x] 05 Tenant Context Resolver (contextvars)
- [x] 06 Users, Sessions & MFA Identity Models
- [x] 07 Roles, Permissions & Scopes (RBAC)
- [x] 08 PostgreSQL Row Level Security (RLS) setup
- [x] 09 Audit Logging (Immutable ledger)
- [x] 10 Idempotency Engine
- [x] 11 CI/CD (GitHub Actions)
- [x] 12 Schema Linter & Architecture Fitness Tests

## Milestone: CORE DOMAIN

### Wave 1 — Gym Core - 🟠 PARTIAL (Models Only)
- [x] Locations & Facilities models
- [x] Staff / TenantUser linking model
- [x] Members Core (Profiles, PII classification)
- [x] Member 360 (Tags & Notes)
- [x] Consent Registry (ADR-016)
- [ ] Documents & Secure File Storage (ADR-034)
- [ ] Import Engine Basics
- [ ] API & Services Layer

### Wave 2 — Membership - 🟠 PARTIAL (Models Only)
- [x] Plans & Plan Versions
- [x] Subscriptions / Periods
- [x] Freeze / Renew / Cancel Lifecycle
- [x] Usage Wallets & Entitlements
- [x] Access Policies
- [ ] API & Services Layer

### Wave 3 — Finance - 🟠 PARTIAL (Models Only)
- [x] Billing Accounts
- [x] Invoices & Invoice Items
- [x] Payments & Allocations
- [x] Partial Payments
- [x] Refund, Credit & Discount Logic
- [x] Reconciliation
- [ ] API & Services Layer

### Wave 4 — Access - 🟠 PARTIAL (Models Only)
- [x] QR Credential Issuer & Key Rotation (ADR-024) (Database Models)
- [x] Access Decision Engine (Database Models)
- [x] Device Heartbeats & Offline Gateway Interface (Database Models)
- [x] Anti-passback & Attendance Logic (Database Models)
- [x] Scanner PWA Basics & Gateway Apps
- [x] Secret Manager Integration for Key Material
- [ ] API & Services Layer

### Wave 5 — Operational MVP - 🟠 PARTIAL (Models Only)
- [x] Report Engine (Runs, Exports) (Database Models)
- [x] Notifications & Deliveries (Database Models)
- [x] Scheduled Jobs (Outbox/Inbox) (Database Models)
- [ ] Gym & Federation Dashboards
- [ ] Support / Operations Console
- [ ] API & Services Layer

## Milestone: CORE HARDENING (Wave 5.5) - ✅ COMPLETED
- [x] Real PostgreSQL RLS cross-tenant tests
- [x] Authenticated tenant resolver (from user + membership)
- [x] Real session/user implementation
- [x] Composite tenant FK constraints enforced in migrations
- [x] Secret-manager integration for signing keys (no plaintext in DB)
- [x] Real domain services & APIs for Core Models
- [x] Real QR issuer/verifier/replay pipeline
- [x] Fix CI pipeline and enforce main branch protection

## Milestone: GROWTH & SCALE

### Wave 6 — Growth - 🟠 PARTIAL (Models Only)
- [x] Lead CRM & Opportunities
- [x] Renewal Pipeline & Revenue Recovery
- [x] Member Health & Retention Cockpit
- [x] Tasks & Automations
- [ ] API & Services Layer

### Wave 7 — Federation - 🟠 PARTIAL (Models Only)
- [x] Gym Passport
- [x] Compliance & Certification
- [x] Network Alerts & Benchmark
- [ ] API & Services Layer

### Wave 8 — Platform - 📝 PENDING
- [ ] SaaS Billing & Metering (ADR-028)
- [ ] Feature Entitlements & Quotas
- [ ] White Label & Custom Domains
- [ ] Public API & Integration Marketplace (ADR-026)

### Wave 9 & 10 — Network & Intelligence - 📝 PENDING
- [ ] Cross-gym Access & Corporate Memberships
- [ ] Predictive Analytics (Churn, Capacity, Revenue)
