# Phase 18 — Vertical Slice E2E (Access)

**Status:** 🟡 PARTIAL (service-layer slice landed; HTTP/API orchestration deferred)  
**Plan path:** `backend/docs/plans/phase18_vertical_slice_e2e.md`  
**Test path:** `backend/tests/e2e/test_vertical_slice_access.py`  
**Depends on:** Phase 13 QR access, Phase 14 member/gym core, Phase 15.5 trust boundaries, Phase 16 NotificationBridge helper  
**Do not claim:** production-ready / full Admin MVP

---

## Goal

Prove one **happy-path vertical slice** on real PostgreSQL:

```text
Organization + Tenant
  → User (MEMBER role + session token_hash)
  → Member bound via user_id
  → ACTIVE membership + GYM_ENTRY wallet
  → issue-self resolution (server-owned member lookup)
  → AccessService.issue_qr_token
  → AccessService.validate_qr → GRANT + AccessAttempt + Checkin
  → (optional) NotificationBridge.schedule_for_member_user
       → NotificationDelivery QUEUED + outbox notification.requested.v1
```

This is **not** a claim that Phase 18 Admin MVP or full API E2E is done — only that the core access domain chain is exerciseable end-to-end at the service layer.

---

## What passes (landed)

| Case | Coverage |
|------|----------|
| `test_vertical_slice_org_member_qr_issue_validate` | Org/tenant seed → MEMBER user + `UserSession` (phase15.5c token pattern) → `MemberService.create_member(..., user_id=)` → issue-self resolve via `get_member_by_user_id` → lazy signing key → issue QR → `validate_qr` GRANT with location + `GYM_ENTRY` → `AccessAttempt` GRANTED |
| `test_vertical_slice_staff_issue_validate_structured` | Explicit `member_id` issue path + structured `ValidateQrResult` (malformed deny + grant) |
| `test_vertical_slice_optional_notification_bridge` | Bridge schedules EMAIL delivery for bound user without importing notification into MembershipService; outbox `notification.requested.v1` |

**Fixtures:** session-scoped Alembic migrations via `pg_engine` (`tests/conftest.py`); per-test TRUNCATE; superuser DB URL (same as other service tests).

**Signing keys:** no pre-seed required — `AccessService.ensure_active_key` mints tenant-scoped `ACTIVE` HMAC key on first issue (see `tests/services/test_access_qr.py`).

---

## Gaps (explicit non-goals for this slice)

| Gap | Notes |
|-----|--------|
| **HTTP / ASGI E2E** | No `AsyncClient` calls to `POST /access/qr/issue-self` or `/access/qr/validate`. Auth middleware + RBAC on those routes are covered separately in unit/API tests. |
| **MEMBER HTTP BOLA** | issue-self API + `require_self` proven in phase15.5c / access endpoint unit paths; not re-asserted here via HTTP. |
| **MembershipService → outbox → consumer → bridge** | Bridge is called **directly** from the test (orchestrator stand-in). MembershipService must **not** import notification* (architecture gate). Real consumer wiring remains Phase 17/18 orchestration work. |
| **Payment / finance chain** | No invoice, payment capture, or membership activation from payment. Membership + wallet are seeded directly ACTIVE. |
| **Entitlement consume** | validate uses default `consume=False`; wallet remaining not decremented. |
| **Device / location hardware** | Location is a DB row only; no device adapter, ZKTeco, offline snapshot. |
| **Replay / rotation / revoke** | Covered in `tests/services/test_access_qr.py`, not duplicated in this slice. |
| **Multi-tenant isolation E2E** | Cross-tenant kid deny exists in access unit tests; not in this slice. |
| **Real providers** | Notification uses template + outbox only; no Email/WhatsApp/SMS provider delivery. |
| **app_user RLS runtime path** | This slice uses migrator/superuser session (like most service tests). RLS `app_user` GUC paths live in tenancy isolation tests. |

---

## How to run

```bash
cd backend
# Compose maps Postgres to host :5433 (conftest default is :5432)
export TEST_DATABASE_URL='postgresql+asyncpg://postgres:postgres@localhost:5433/fitness_test_db'
export TEST_RUNTIME_DATABASE_URL='postgresql+asyncpg://app_user:app_password@localhost:5433/fitness_test_db'
uv run pytest tests/e2e/test_vertical_slice_access.py -q
```

**Verified:** 3 passed (2026-08-10) against Docker `fitness-os-postgres:5433`.

---

## Hard rules respected

- Federation ≠ Tenant; Gym = Tenant; Branch = Location
- User ≠ Member (binding via `members.user_id`)
- issue-self never accepts client `member_id` (service resolve only)
- Money as minor units on seeded plan version (`price_amount_minor`)
- Domain → Notification only via NotificationBridge / outbox (not Membership → channel)
- Dynamic short-lived signed QR + jti replay tables (engine from Phase 13)

---

## Next steps (when Phase 18 expands)

1. HTTP vertical slice with `api_client` + MEMBER bearer + staff validate permission.
2. Wire domain-event consumer: `membership.activated.v1` → `NotificationBridge` (not inside MembershipService).
3. Optional: activate membership via finance payment path once Phase 18 staff surfaces need it.
4. Promote slice to CI required path when HTTP coverage lands.
