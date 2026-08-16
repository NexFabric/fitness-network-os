# Dependency Graph

## Most Imported Files (change these carefully)

- `backend/app/models/user.py` — imported by **73** files
- `backend/app/models/tenant.py` — imported by **67** files
- `backend/app/models/organization.py` — imported by **60** files
- `backend/app/api/deps.py` — imported by **47** files
- `backend/app/models/member.py` — imported by **45** files
- `backend/app/models/rbac.py` — imported by **44** files
- `backend/app/db/base.py` — imported by **38** files
- `backend/app/db/session.py` — imported by **35** files
- `backend/app/main.py` — imported by **30** files
- `frontend/admin-web/src/components/ui/index.ts` — imported by **30** files
- `backend/app/models/membership.py` — imported by **29** files
- `frontend/admin-web/src/api/client.ts` — imported by **27** files
- `backend/app/models/location.py` — imported by **26** files
- `backend/app/core/authorization.py` — imported by **25** files
- `backend/app/db/rls.py` — imported by **22** files
- `backend/app/core/config.py` — imported by **20** files
- `backend/app/models/access.py` — imported by **19** files
- `backend/app/models/outbox.py` — imported by **17** files
- `frontend/e2e/tests/helpers/auth.ts` — imported by **17** files
- `backend/app/models/finance.py` — imported by **16** files

## Import Map (who imports what)

- `backend/app/models/user.py` ← `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/access.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/break_glass.py`, `backend/app/api/v1/endpoints/classes.py` +68 more
- `backend/app/models/tenant.py` ← `backend/app/api/deps.py`, `backend/app/models/__init__.py`, `backend/app/services/federation.py`, `backend/app/services/resolution.py`, `backend/app/workers/notification.py` +62 more
- `backend/app/models/organization.py` ← `backend/app/models/__init__.py`, `backend/app/services/federation.py`, `backend/scripts/seed_demo_tenant.py`, `backend/scripts/seed_role_matrix.py`, `backend/tests/api/test_admin_federation.py` +55 more
- `backend/app/api/deps.py` ← `backend/app/api/v1/endpoints/access.py`, `backend/app/api/v1/endpoints/admin.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/break_glass.py`, `backend/app/api/v1/endpoints/classes.py` +42 more
- `backend/app/models/member.py` ← `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/dashboard.py`, `backend/app/api/v1/endpoints/reception.py`, `backend/app/models/__init__.py`, `backend/app/services/access.py` +40 more
- `backend/app/models/rbac.py` ← `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/onboarding.py`, `backend/app/models/__init__.py`, `backend/app/models/user.py` +39 more
- `backend/app/db/base.py` ← `backend/alembic/env.py`, `backend/app/models/access.py`, `backend/app/models/audit.py`, `backend/app/models/booking.py`, `backend/app/models/break_glass.py` +33 more
- `backend/app/db/session.py` ← `backend/app/api/deps.py`, `backend/app/api/v1/endpoints/memberships.py`, `backend/app/api/v1/endpoints/plans.py`, `backend/app/main.py`, `backend/app/workers/notification.py` +30 more
- `backend/app/main.py` ← `backend/tests/api/test_admin_federation.py`, `backend/tests/api/test_admin_federation_complete.py`, `backend/tests/api/test_adversarial_security.py`, `backend/tests/api/test_auth_login.py`, `backend/tests/api/test_class_booking_engine.py` +25 more
- `frontend/admin-web/src/components/ui/index.ts` ← `frontend/admin-web/src/components/MemberMemberships.tsx`, `frontend/admin-web/src/components/RequireAuth.tsx`, `frontend/admin-web/src/pages/Classes.tsx`, `frontend/admin-web/src/pages/Dashboard.tsx`, `frontend/admin-web/src/pages/DataImport.tsx` +25 more
