# OWASP ASVS 5.0 Level 2 — Preparatory Self-Assessment

**Project:** GymClubNex (Fitness Network OS)
**Date:** 2026-08-12
**Target Level:** ASVS 5.0 Level 2 (sensitive business data / multi-tenant SaaS)
**Status:** **SELF-ASSESSED — NOT INDEPENDENTLY VERIFIED**

> This document records what the team believes it has implemented, checked
> against the code. It is **not** an audit result. No external penetration test
> has been performed and no independent reviewer has signed off — see
> `docs/ops/ASVS_PENTEST_STATUS.md`, which gates Phase 26 on exactly that
> evidence. Do not cite this file as proof of a passed security review.

> The evidence below is grouped by control family, not asserted as a complete
> normative control-ID mapping. The independent reviewer must map the final
> ASVS 5.0 catalogue and attach findings before this becomes an acceptance artifact.

---

## 1. Architecture, Design and Threat Modeling
- [x] Multi-tenant isolation enforced at the database layer via PostgreSQL RLS with `FORCE ROW LEVEL SECURITY`; context set transaction-scoped (`SET LOCAL app.current_tenant_id`) and re-armed after commit (`app/db/session.py`).
- [x] Modular monolith (Auth, Gym Core, Access, Finance, Outbox). No unauthenticated internal inter-service channels.
- [x] `device_sessions` carries `tenant_id` but deliberately has no RLS policy: it is the bootstrap lookup that *derives* the tenant, so a tenant policy there would fail closed on every device request. It is the only pre-context read — `devices` and `device_nonces` are queried after `SET LOCAL app.current_tenant_id` and keep full RLS. The session cookie hash is stored as SHA-256. Signing material is Fernet-wrapped (`fernet:hmac:`) under `ENCRYPTION_KEY`; a cookie alone is still not a usable credential (ADR-044).

## 2. Authentication
- [x] Password storage uses Argon2id (`passlib.context.CryptContext`). No MD5/SHA1 legacy hashes.
- [x] MFA TOTP via RFC 6238 (`pyotp`), secret stored Fernet-encrypted.
- [x] Single-use emergency recovery codes issued at enrollment.

## 3. Session Management
- [x] Session identifier lives only in a `HttpOnly`, `Secure`, `SameSite=Lax` cookie.
- [x] No raw session secret in `localStorage`/`sessionStorage`. The browser stores the tenant id only. The scanner's device signing secret is held as a non-extractable `CryptoKey` handle in IndexedDB — signable, unreadable, never persisted as plaintext.

## 4. Access Control
- [x] RBAC matrix of 11 canonical roles enforced at the FastAPI layer. Roles are `PLATFORM_SUPER_ADMIN`, `FEDERATION_ADMIN`, `FEDERATION_ANALYST`, `FEDERATION_SUPPORT`, `GYM_OWNER`, `GYM_ADMIN`, `GYM_MANAGER`, `ACCOUNTANT`, `FRONT_DESK`, `TRAINER`, `MEMBER` (`backend/permissions.yml`, `app/core/authorization.py`). Source of truth is CI-checked against the database (`scripts/check_permissions_db.py`).
- [x] Object-level authorization: `*:self` permissions require ownership proof, never tenant match alone (`AuthorizationService.require_self`). `POST /access/qr/issue-self` accepts no `member_id` and resolves the member from the session.
- [x] Row-level scoping for trainers: `members:read` grants the call, `members:read:all` grants the whole tenant. TRAINER holds only the former and is restricted to `trainer_assignments` rows.
- [x] Device principals authenticate with `{device_id, tenant_id, api_key}` against a SHA-256 stored hash using constant-time comparison, receiving a `device_session` HttpOnly cookie. Device-side endpoints ignore client-supplied `device_id`/`location_id` and substitute the trusted device's own.
- [x] The device channel requires HMAC-SHA256 request signing. `POST /devices/auth` returns a per-session signing secret in the response body (never a cookie); every device request must carry `X-Device-Signature` over `METHOD\npath\ntimestamp\nnonce\nsha256(body)`, within a ±300s clock-skew window, with a single-use nonce recorded in `device_nonces`. A stolen `device_session` cookie is therefore no longer a usable credential on its own, and a captured signed request cannot be replayed. Sessions issued before this change fail closed (`device_session_unsigned`) and must re-authenticate. Implementation: `app/core/device_auth.py`, `app/api/deps.py::_verify_device_signature`. Regression: `tests/api/test_scanner_device_auth.py::test_device_request_signing_is_enforced` (cookie-only, forged signature, body mismatch, stale timestamp, nonce replay) and `::test_device_session_without_signing_material_is_rejected`.

- [x] The one unauthenticated write (`POST /auth/login`) is rate limited on a
sliding window held in Redis, so the budget is shared across API processes rather than
multiplied by them. Keyed by the login identifier (hashed — no email reaches Redis or the
logs), never by IP, since NAT co-tenants share an address. A Redis outage degrades to a
bounded in-process window and logs it, rather than taking login down.
Regression: `tests/api/test_rate_limit.py` (per-identifier budget, 429 shape, hashed key,
cache-outage fallback, shared window across two instances).

## 5. Financial & Input Validation
- [x] Pydantic models at every API boundary; money is integer `amount_minor` (kuruş) throughout — float money fields are CI-blocked (`scripts/check_no_money_floats.py`).
- [x] Anti-CSRF double-submit validation for non-exempt state-changing routes.
- [x] The `Authorization: Bearer` CSRF exemption applies only when no `session_token` cookie is present (`app/api/middleware/csrf.py`). Because `get_session_token_from_cookie` prefers the cookie, a request carrying both authenticates ambiently, so an attacker-supplied header can no longer waive the check. Regression: `tests/api/test_csrf_bootstrap.py::test_bearer_header_does_not_waive_csrf_when_session_cookie_present`.

---

## Verdict

**Not a pass.** Every checklist item above is now closed with code and a regression test, but this is
self-assessment only: no independent verification has taken place. Phase 26 remains **NOT PASSED**
until an external penetration test report is attached and an APPROVE is recorded per
`ASVS_PENTEST_STATUS.md`.
