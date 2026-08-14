# Dependency Graph

## Most Imported Files (change these carefully)

- `backend/app/models/user.py` — imported by **51** files
- `backend/app/models/tenant.py` — imported by **45** files
- `backend/app/models/organization.py` — imported by **39** files
- `backend/app/db/base.py` — imported by **36** files
- `backend/app/api/deps.py` — imported by **36** files
- `backend/app/models/member.py` — imported by **35** files
- `backend/app/models/rbac.py` — imported by **30** files
- `backend/app/db/session.py` — imported by **24** files
- `backend/app/models/membership.py` — imported by **24** files
- `backend/app/core/authorization.py` — imported by **22** files
- `frontend/admin-web/src/api/client.ts` — imported by **21** files
- `backend/app/main.py` — imported by **20** files
- `backend/app/db/rls.py` — imported by **19** files
- `backend/app/core/config.py` — imported by **17** files
- `backend/app/models/access.py` — imported by **14** files
- `backend/app/models/location.py` — imported by **14** files
- `frontend/admin-web/src/components/ui/index.ts` — imported by **14** files
- `backend/app/models/entitlement.py` — imported by **12** files
- `backend/app/models/outbox.py` — imported by **12** files
- `backend/app/models/finance.py` — imported by **11** files

## Import Map (who imports what)

- `backend/app/models/user.py` ← `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/access.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/dashboard.py`, `backend/app/api/v1/endpoints/data_import.py` +46 more
- `backend/app/models/tenant.py` ← `backend/app/api/deps.py`, `backend/app/models/__init__.py`, `backend/app/services/federation.py`, `backend/app/services/resolution.py`, `backend/app/workers/notification.py` +40 more
- `backend/app/models/organization.py` ← `backend/app/models/__init__.py`, `backend/app/services/federation.py`, `backend/scripts/seed_demo_tenant.py`, `backend/scripts/seed_role_matrix.py`, `backend/tests/api/test_admin_federation.py` +34 more
- `backend/app/db/base.py` ← `backend/alembic/env.py`, `backend/app/models/access.py`, `backend/app/models/audit.py`, `backend/app/models/break_glass.py`, `backend/app/models/consent.py` +31 more
- `backend/app/api/deps.py` ← `backend/app/api/v1/endpoints/access.py`, `backend/app/api/v1/endpoints/admin.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/dashboard.py`, `backend/app/api/v1/endpoints/data_import.py` +31 more
- `backend/app/models/member.py` ← `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/dashboard.py`, `backend/app/api/v1/endpoints/reception.py`, `backend/app/models/__init__.py`, `backend/app/services/access.py` +30 more
- `backend/app/models/rbac.py` ← `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/models/__init__.py`, `backend/app/models/user.py`, `backend/app/services/notification.py` +25 more
- `backend/app/db/session.py` ← `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/memberships.py`, `backend/app/api/v1/endpoints/plans.py`, `backend/app/main.py`, `backend/app/workers/notification.py` +19 more
- `backend/app/models/membership.py` ← `backend/app/api/v1/endpoints/dashboard.py`, `backend/app/api/v1/endpoints/reception.py`, `backend/app/models/__init__.py`, `backend/app/services/data_import.py`, `backend/app/services/entitlement.py` +19 more
- `backend/app/core/authorization.py` ← `backend/app/api/v1/endpoints/access.py`, `backend/app/api/v1/endpoints/dashboard.py`, `backend/app/api/v1/endpoints/data_import.py`, `backend/app/api/v1/endpoints/devices.py`, `backend/app/api/v1/endpoints/entitlements.py` +17 more
