# Admin

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Admin subsystem handles **17 routes** and touches: auth, db.

## Routes

- `GET` `/organizations` → in: FederationScop, out: list
  `backend/app/api/v1/endpoints/admin.py`
- `GET` `/tenants` → in: FederationScop, out: list
  `backend/app/api/v1/endpoints/admin.py`
- `POST` `/tenants` → in: TenantCreateRequest, out: list [auth]
  `backend/app/api/v1/endpoints/admin.py`
- `GET` `/tenants/{tenant_id}` params(tenant_id) → in: FederationScop, out: list
  `backend/app/api/v1/endpoints/admin.py`
- `POST` `/tenants/{tenant_id}/suspend` params(tenant_id) → in: TenantCreateRequest, out: list
  `backend/app/api/v1/endpoints/admin.py`
- `POST` `/tenants/{tenant_id}/reactivate` params(tenant_id) → in: TenantCreateRequest, out: list
  `backend/app/api/v1/endpoints/admin.py`
- `GET` `/federation/summary` → in: FederationScop, out: list
  `backend/app/api/v1/endpoints/admin.py`
- `GET` `/audit` → in: FederationScop, out: list
  `backend/app/api/v1/endpoints/admin.py`
- `GET` `/passport/configs` → in: FederationScop, out: list [auth]
  `backend/app/api/v1/endpoints/admin.py`
- `GET` `/tenants/{tenant_id}/passport` params(tenant_id) → in: FederationScop, out: list [auth]
  `backend/app/api/v1/endpoints/admin.py`
- `PUT` `/tenants/{tenant_id}/passport` params(tenant_id) → in: UUID, out: list [auth]
  `backend/app/api/v1/endpoints/admin.py`
- `GET` `/compliance` → in: FederationScop, out: list
  `backend/app/api/v1/endpoints/admin.py`
- `POST` `/tenants/{tenant_id}/compliance` params(tenant_id) → in: TenantCreateRequest, out: list
  `backend/app/api/v1/endpoints/admin.py`
- `GET` `/alerts` → in: FederationScop, out: list
  `backend/app/api/v1/endpoints/admin.py`
- `POST` `/alerts` → in: TenantCreateRequest, out: list
  `backend/app/api/v1/endpoints/admin.py`
- `DELETE` `/alerts/{alert_id}` params(alert_id) → in: UUID, out: list [db]
  `backend/app/api/v1/endpoints/admin.py`
- `GET` `/analytics/overview` → in: FederationScop, out: list
  `backend/app/api/v1/endpoints/admin.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/admin.py`

---
_Back to [overview.md](./overview.md)_