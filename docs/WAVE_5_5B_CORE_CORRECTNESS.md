# FITNESS NETWORK OS — WAVE 5.5B CORE CORRECTNESS & EXECUTABLE MVP

> **Archive note (2026-08-09):** Phase **0–15** are CI VERIFIED / LOCKED on `main`.  
> Live progress: `docs/PROGRESS_CHECKLIST.md` · next **Phase 16**. This file remains historical guidance for Wave 5.5B intent; do not use it as current phase status.

This document supersedes previous rapid-development instructions. The goal is to harden the existing models into a true, executable MVP.

## CORE PRINCIPLE
A model/table existing does NOT mean a feature is complete. All features must be evaluated on a 3-tier maturity scale:
- MODEL: Database tables and migrations exist.
- SERVICE/API: Business logic and API endpoints exist.
- PRODUCTION VERIFIED: Fully tested (integration/E2E), authorized, and CI-gated.

---

## PHASE 0 — STATUS TRUTH & CI RECOVERY
- Verify `main` HEAD.
- Verify Alembic migration chain.
- Run tests against a REAL PostgreSQL database.
- Fix the CI pipeline (resolve billing/running issues).
- Execute Gitleaks, Bandit, pip-audit, Ruff, Mypy.

## PHASE 1 — MAIN BRANCH PROTECTION
- Enforce via GitHub API: `main` is protected, requires PRs, requires status checks (Security, Lint, Tests).

## PHASE 2 — AUTHENTICATION & SESSION P0
- Remove dummy `password + "_hashed"`. Implement Argon2id password hashing.
- Session tokens must be cryptographically random, hashed in DB.
- Remove `if token == "test-token"` bypasses in production code.
- Implement Secure, HttpOnly, SameSite cookies with CSRF protection.

## PHASE 3 — MFA & PRIVILEGED AUTH
- Remove plaintext MFA secrets. Implement encryption/provider abstraction.
- Build foundation for TOTP, recovery codes, and step-up auth.

## PHASE 4 — TENANT CONTEXT & REAL RLS BOUNDARY
- Separate DB Roles: Admin/Migration role vs Runtime Role (`NOSUPERUSER`, `NOBYPASSRLS`).
- Authentication flow: Global Session -> Auth User -> Authorized Tenant -> Tenant Scoped Session -> `SET LOCAL app.current_tenant_id`.
- Tenant context MUST NOT be blindly trusted from `X-Tenant-ID` header.
- RLS Tests MUST run as the `NOSUPERUSER` runtime role to prove isolation.

## PHASE 5 — TENANCY SCHEMA LINTER V2
- Upgrade linter to enforce: `tenant_id NOT NULL`, index, RLS enabled, `FORCE ROW LEVEL SECURITY`, `USING` policy, `WITH CHECK` policy, `UNIQUE(tenant_id, id)`, and composite tenant FKs.

## PHASE 6 — COMPLETE COMPOSITE FK COVERAGE
- Ensure all tenant-owned relationships use `(tenant_id, foreign_id)` composite foreign keys.
- Specifically target: PlanVersion->Plan, Membership->Member, Entitlement->Member, Consents, Staff, Opportunities, Tasks, etc.

## PHASE 7 — AUTHORIZATION ENGINE
- Remove `.get("permissions")` dummy dict accesses. Use the real SQLAlchemy User model.
- Implement RBAC + Scopes (SELF, ASSIGNED, LOCATION, TENANT, PLATFORM).
- Generate automatic ALLOW/DENY tests from the permission matrix.
- Ensure the `core` layer does not import the `api` layer.

## EXECUTION INSTRUCTIONS FOR AGENTS
Do not jump ahead to Phase 8. Ensure Phases 0-7 are perfectly executed, tested, and pushed before signaling completion. All branches must be tested before merging.
