# Phase 8 Deep-Dive Fix Plan

## 1. Cleanup & Easy Wins
- [x] Delete `pytest_error.log`, `pytest_failure.log`, `pytest_output.log` and add to `.gitignore`.
- [x] Fix Pydantic v2 `class Config` to `model_config = ConfigDict(from_attributes=True)`.
- [x] Fix SQLAlchemy overlapping relationship warnings.

## 2. Test Infrastructure & Tenancy
- [x] Modify `tests/conftest.py` to NOT use `Base.metadata.create_all()`. It should rely on `alembic upgrade head`. Use TRUNCATE or transactions to clean data between tests.
- [x] Verify `trufflehog` in `.github/workflows/ci.yml` is pinned to a valid version (done?).

## 3. RBAC & Migrations Separation
- [x] Review `dd603a516953` (RBAC), `0a561fd73793` (Core/RBAC update), and `db8f4db0e58d` (Phase 8 Membership) migrations.
- [x] Move `organization_id` and `tenant_id` nullable changes for `UserRole` out of the Membership migration into a dedicated RBAC migration.
- [x] Add DB Check constraint to `UserRole` to prevent both `tenant_id` and `organization_id` being set.
- [x] Add explicit DB synchronization/seeding mechanism from `permissions.yml`.

## 4. Phase 8 Domain Completion (Membership)
- [x] Rename `subscription_periods` -> `membership_periods`.
- [x] Rename `status_history` -> `membership_status_history`.
- [x] Add `MembershipCancellation`, `MembershipRenewal` models/tables.
- [x] Update `PlanVersion` to be immutable and published, with `price_snapshot` and `terms_snapshot` in Membership.
- [x] Add explicit lifecycle state machine (DRAFT -> PENDING -> SCHEDULED -> ACTIVE -> FROZEN/PAST_DUE -> CANCELLED/EXPIRED).
- [x] Implement `start`, `schedule`, `freeze`, `unfreeze`, `renew`, `cancel`, `expire`, `past_due` methods in service.
- [x] Define overlap/stackability policy.
- [x] Fix concurrency: Add `SELECT FOR UPDATE` or optimistic locking, DB unique invariants for active freeze.

## 5. RLS Policies
- [x] Add `enable_rls(...)` to ALL new Phase 8 tables in their migration: `membership_freezes`, `membership_status_history`, `membership_periods`, `membership_cancellations`, `membership_renewals`.

## 6. Authorization & API Security
- [x] Add `AuthorizationService.is_authorized(permission="memberships:write")` to Membership API endpoints (freeze/unfreeze etc.).
- [x] Write cross-tenant negative API tests with runtime roles.
- [x] Write concurrent freeze/unfreeze tests.

## 7. Service Transaction Boundary
- [x] Ensure Service methods do not prematurely commit, but return or manage transactions at the Application level (or use atomic blocks).
