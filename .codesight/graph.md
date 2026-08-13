# Dependency Graph

## Most Imported Files (change these carefully)

- `backend/app/models/user.py` — imported by **42** files
- `backend/app/models/tenant.py` — imported by **38** files
- `backend/app/models/organization.py` — imported by **33** files
- `backend/app/db/base.py` — imported by **32** files
- `backend/app/api/deps.py` — imported by **30** files
- `backend/app/models/member.py` — imported by **30** files
- `backend/app/models/rbac.py` — imported by **26** files
- `backend/app/db/session.py` — imported by **21** files
- `backend/app/models/membership.py` — imported by **20** files
- `backend/app/db/rls.py` — imported by **18** files
- `backend/app/core/authorization.py` — imported by **18** files
- `frontend/admin-web/src/api/client.ts` — imported by **17** files
- `backend/app/main.py` — imported by **16** files
- `backend/app/core/config.py` — imported by **12** files
- `backend/app/models/location.py` — imported by **12** files
- `backend/app/models/outbox.py` — imported by **12** files
- `frontend/admin-web/src/components/ui/index.ts` — imported by **12** files
- `backend/app/models/access.py` — imported by **11** files
- `backend/app/models/entitlement.py` — imported by **10** files
- `backend/app/services/outbox.py` — imported by **10** files

## Import Map (who imports what)

- `backend/app/models/user.py` ← `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/access.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/devices.py`, `backend/app/api/v1/endpoints/entitlements.py` +37 more
- `backend/app/models/tenant.py` ← `backend/app/models/__init__.py`, `backend/app/services/federation.py`, `backend/app/services/resolution.py`, `backend/app/workers/notification.py`, `backend/app/workers/report.py` +33 more
- `backend/app/models/organization.py` ← `backend/app/models/__init__.py`, `backend/app/services/federation.py`, `backend/scripts/seed_demo_tenant.py`, `backend/scripts/seed_role_matrix.py`, `backend/tests/api/test_admin_federation.py` +28 more
- `backend/app/db/base.py` ← `backend/alembic/env.py`, `backend/app/models/access.py`, `backend/app/models/audit.py`, `backend/app/models/consent.py`, `backend/app/models/entitlement.py` +27 more
- `backend/app/api/deps.py` ← `backend/app/api/v1/endpoints/access.py`, `backend/app/api/v1/endpoints/admin.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/devices.py`, `backend/app/api/v1/endpoints/entitlements.py` +25 more
- `backend/app/models/member.py` ← `backend/app/api/v1/endpoints/auth.py`, `backend/app/models/__init__.py`, `backend/app/services/access.py`, `backend/app/services/federation.py`, `backend/app/services/finance.py` +25 more
- `backend/app/models/rbac.py` ← `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/models/__init__.py`, `backend/app/models/user.py`, `backend/app/services/notification.py` +21 more
- `backend/app/db/session.py` ← `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/memberships.py`, `backend/app/api/v1/endpoints/plans.py`, `backend/app/main.py`, `backend/app/workers/notification.py` +16 more
- `backend/app/models/membership.py` ← `backend/app/models/__init__.py`, `backend/app/services/entitlement.py`, `backend/app/services/federation.py`, `backend/app/services/membership.py`, `backend/app/services/resolution.py` +15 more
- `backend/app/db/rls.py` ← `backend/alembic/versions/0a561fd73793_update_rbac_models.py`, `backend/alembic/versions/32bea30c0ed8_add_federation_models.py`, `backend/alembic/versions/45e716039e1c_add_phase_8_membership_domain_models.py`, `backend/alembic/versions/67eca287af30_add_operational_mvp_models.py`, `backend/alembic/versions/8d4b31a89f92_add_growth_and_crm_models.py` +13 more
