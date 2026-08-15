# Dependency Graph

## Most Imported Files (change these carefully)

- `backend/app/models/user.py` — imported by **58** files
- `backend/app/models/tenant.py` — imported by **53** files
- `backend/app/models/organization.py` — imported by **46** files
- `backend/app/api/deps.py` — imported by **44** files
- `backend/app/db/base.py` — imported by **37** files
- `backend/app/models/member.py` — imported by **37** files
- `backend/app/models/rbac.py` — imported by **33** files
- `backend/app/db/session.py` — imported by **27** files
- `backend/app/models/membership.py` — imported by **27** files
- `backend/app/core/authorization.py` — imported by **23** files
- `backend/app/main.py` — imported by **22** files
- `frontend/admin-web/src/api/client.ts` — imported by **22** files
- `backend/app/db/rls.py` — imported by **20** files
- `backend/app/models/location.py` — imported by **20** files
- `backend/app/core/config.py` — imported by **18** files
- `backend/app/models/access.py` — imported by **18** files
- `backend/app/models/outbox.py` — imported by **16** files
- `frontend/admin-web/src/components/ui/index.ts` — imported by **15** files
- `backend/app/models/finance.py` — imported by **13** files
- `backend/app/core/event_types.py` — imported by **13** files

## Import Map (who imports what)

- `backend/app/models/user.py` ← `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/access.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/break_glass.py`, `backend/app/api/v1/endpoints/classes.py` +53 more
- `backend/app/models/tenant.py` ← `backend/app/api/deps.py`, `backend/app/models/__init__.py`, `backend/app/services/federation.py`, `backend/app/services/resolution.py`, `backend/app/workers/notification.py` +48 more
- `backend/app/models/organization.py` ← `backend/app/models/__init__.py`, `backend/app/services/federation.py`, `backend/scripts/seed_demo_tenant.py`, `backend/scripts/seed_role_matrix.py`, `backend/tests/api/test_admin_federation.py` +41 more
- `backend/app/api/deps.py` ← `backend/app/api/v1/endpoints/access.py`, `backend/app/api/v1/endpoints/admin.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/break_glass.py`, `backend/app/api/v1/endpoints/classes.py` +39 more
- `backend/app/db/base.py` ← `backend/alembic/env.py`, `backend/app/models/access.py`, `backend/app/models/audit.py`, `backend/app/models/booking.py`, `backend/app/models/break_glass.py` +32 more
- `backend/app/models/member.py` ← `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/dashboard.py`, `backend/app/api/v1/endpoints/reception.py`, `backend/app/models/__init__.py`, `backend/app/services/access.py` +32 more
- `backend/app/models/rbac.py` ← `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/onboarding.py`, `backend/app/models/__init__.py`, `backend/app/models/user.py` +28 more
- `backend/app/db/session.py` ← `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/memberships.py`, `backend/app/api/v1/endpoints/plans.py`, `backend/app/main.py`, `backend/app/workers/notification.py` +22 more
- `backend/app/models/membership.py` ← `backend/app/api/v1/endpoints/dashboard.py`, `backend/app/api/v1/endpoints/onboarding.py`, `backend/app/api/v1/endpoints/reception.py`, `backend/app/models/__init__.py`, `backend/app/services/access.py` +22 more
- `backend/app/core/authorization.py` ← `backend/app/api/v1/endpoints/access.py`, `backend/app/api/v1/endpoints/classes.py`, `backend/app/api/v1/endpoints/dashboard.py`, `backend/app/api/v1/endpoints/data_import.py`, `backend/app/api/v1/endpoints/devices.py` +18 more
