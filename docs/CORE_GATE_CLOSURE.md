# CORE GATE CLOSURE — PHASE 0–7 FINAL VERIFICATION

This document outlines the final gate closures required before moving to Phase 8. DO NOT PROCEED TO PHASE 8 until all items here are completely finished and verified in CI.

## P0-1 — MAIN BRANCH PROTECTION
- Use GitHub API to enforce: `protected = true`, `pull request required`, `required status checks`, `force push disabled`, `branch deletion disabled`, `direct push disabled`.

## P0-2 — CI MUST BE GREEN
- Fix actual failures in Ruff, Gitleaks, dependency setup, and subsequent jobs.
- Remove `|| true` from security scans (e.g. `pip-audit || true`). Use severity policies instead.

## P0-3 — CI DATABASE CONFIGURATION
- In `ci.yml`, explicitely define both `TEST_DATABASE_URL` and `TEST_RUNTIME_DATABASE_URL` for the pytest steps so that RLS tests connect correctly instead of falling back to a non-existent DB or port.

## P0-4 — AUTH DEPENDENCIES
- `passlib` and `argon2-cffi` (or `passlib[argon2]`) must be explicitly added to `pyproject.toml` dependencies.

## P0-5 — SESSION TOKEN CORRECTNESS
- In `get_current_user`, hash the incoming token FIRST before querying `UserSession.token_hash`.
- Check `expires_at` and `user.is_active` along with `is_revoked`.

## P0-6 — MFA MODEL / MIGRATION DRIFT
- The ORM `UserMfaMethod` expects `provider_id` and `encrypted_secret`, but Alembic created `secret` and `method_type`.
- Create a new explicit Alembic migration to sync the database schema with the ORM.

## P0-7 — REAL RUNTIME DB ROLE
- Stop using `postgres:postgres` for the application runtime in `docker-compose.yml`.
- Separate the migration role (schema owner) from the application role (NOSUPERUSER, NOBYPASSRLS, DML only).

## P0-8 — TENANT SESSION ORDERING
- Fix the dependency injection order. Establish the tenant context BEFORE the `DB query` transaction officially starts to prevent `after_begin` from running without a tenant ID.

## P0-9 — RLS NEGATIVE TEST MATRIX
- Add tests to `test_rls.py`: Tenant A -> Tenant B `INSERT`, `UPDATE`, `DELETE` = denied.
- Missing tenant context = fail closed.
- Spoofed tenant ID = denied.

## P1 — TENANCY LINTER FINALIZATION
- Ensure linter checks for `tenant_id` index, migration/schema drift, and test coverage.

## P1 — AUTHORIZATION MATRIX
- Add full roles: `PLATFORM_SUPER_ADMIN`, `FEDERATION_ADMIN`, `FEDERATION_ANALYST`, `FEDERATION_SUPPORT`, `GYM_OWNER`, `GYM_ADMIN`, `GYM_MANAGER`, `ACCOUNTANT`, `FRONT_DESK`, `TRAINER`, `MEMBER`.
- Add scopes: `SELF`, `ASSIGNED`, `LOCATION`, `TENANT`, `FEDERATION_AGGREGATE`, `PLATFORM`.
- Generate explicit ALLOW/DENY tests for these matrices.
