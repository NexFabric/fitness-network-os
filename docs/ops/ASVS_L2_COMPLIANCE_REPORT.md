# OWASP ASVS 4.0 Level 2 — Self-Assessment

**Project:** GymClubNex (Fitness Network OS)
**Date:** 2026-08-12
**Target Level:** ASVS 4.0.3 Level 2 (sensitive business data / multi-tenant SaaS)
**Status:** **SELF-ASSESSED — NOT INDEPENDENTLY VERIFIED**

> This document records what the team believes it has implemented, checked
> against the code. It is **not** an audit result. No external penetration test
> has been performed and no independent reviewer has signed off — see
> `docs/ops/ASVS_PENTEST_STATUS.md`, which gates Phase 26 on exactly that
> evidence. Do not cite this file as proof of a passed security review.

---

## 1. Architecture, Design and Threat Modeling (V1)
- [x] **1.1.1** Multi-tenant isolation enforced at the database layer via PostgreSQL RLS with `FORCE ROW LEVEL SECURITY`; context set transaction-scoped (`SET LOCAL app.current_tenant_id`) and re-armed after commit (`app/db/session.py`).
- [x] **1.2.1** Modular monolith (Auth, Gym Core, Access, Finance, Outbox). No unauthenticated internal inter-service channels.
- [ ] **Gap:** `device_sessions` carries `tenant_id` but has no RLS policy. It is read before any tenant context exists (`get_current_device`), so a tenant policy there would fail closed on every device request. Currently gated only by a hashed bearer token. Tracked as open.

## 2. Authentication (V2)
- [x] **2.1.1** Password storage uses Argon2id (`passlib.context.CryptContext`). No MD5/SHA1 legacy hashes.
- [x] **2.2.1** MFA TOTP via RFC 6238 (`pyotp`), secret stored Fernet-encrypted.
- [x] **2.2.2** Single-use emergency recovery codes issued at enrollment.

## 3. Session Management (V3)
- [x] **3.4.1** Session identifier lives only in a `HttpOnly`, `Secure`, `SameSite=Lax` cookie.
- [x] **3.4.2** No raw session secret in `localStorage`/`sessionStorage`. The browser stores the tenant id only.

## 4. Access Control (V4)
- [x] **4.1.1** RBAC matrix of 11 canonical roles enforced at the FastAPI layer. Roles are `PLATFORM_SUPER_ADMIN`, `FEDERATION_ADMIN`, `FEDERATION_ANALYST`, `FEDERATION_SUPPORT`, `GYM_OWNER`, `GYM_ADMIN`, `GYM_MANAGER`, `ACCOUNTANT`, `FRONT_DESK`, `TRAINER`, `MEMBER` (`backend/permissions.yml`, `app/core/authorization.py`). Source of truth is CI-checked against the database (`scripts/check_permissions_db.py`).
- [x] **4.2.1** Object-level authorization: `*:self` permissions require ownership proof, never tenant match alone (`AuthorizationService.require_self`). `POST /access/qr/issue-self` accepts no `member_id` and resolves the member from the session.
- [x] **4.2.2** Row-level scoping for trainers: `members:read` grants the call, `members:read:all` grants the whole tenant. TRAINER holds only the former and is restricted to `trainer_assignments` rows.
- [x] **4.3.1** Device principals authenticate with `{device_id, tenant_id, api_key}` against a SHA-256 stored hash using constant-time comparison, receiving a `device_session` HttpOnly cookie. Device-side endpoints ignore client-supplied `device_id`/`location_id` and substitute the trusted device's own.
- [ ] **Gap:** the device channel has no HMAC request signing, nonce, or replay protection; a stolen `device_session` cookie is valid for its 30-day lifetime (revocable via `POST /devices/revoke`). Tracked as open.

## 5. Financial & Input Validation (V5 & V13)
- [x] **5.1.1** Pydantic models at every API boundary; money is integer `amount_minor` (kuruş) throughout — float money fields are CI-blocked (`scripts/check_no_money_floats.py`).
- [x] **13.1.1** Anti-CSRF double-submit validation for non-exempt state-changing routes.
- [x] **13.1.2** The `Authorization: Bearer` CSRF exemption applies only when no `session_token` cookie is present (`app/api/middleware/csrf.py`). Because `get_session_token_from_cookie` prefers the cookie, a request carrying both authenticates ambiently, so an attacker-supplied header can no longer waive the check. Regression: `tests/api/test_csrf_bootstrap.py::test_bearer_header_does_not_waive_csrf_when_session_cookie_present`.

---

## Verdict

**Not a pass.** One gap above is open (device channel replay protection), and no independent verification has
taken place. Phase 26 remains **NOT PASSED** until an external penetration test
report is attached and an APPROVE is recorded per `ASVS_PENTEST_STATUS.md`.
