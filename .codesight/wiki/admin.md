# Admin

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Admin subsystem handles **5 routes**.

## Routes

- `GET` `/organizations` → in: FederationScop, out: list
  `backend/app/api/v1/endpoints/admin.py`
- `GET` `/tenants` → in: FederationScop, out: list
  `backend/app/api/v1/endpoints/admin.py`
- `GET` `/tenants/{tenant_id}` params(tenant_id) → in: FederationScop, out: list
  `backend/app/api/v1/endpoints/admin.py`
- `GET` `/federation/summary` → in: FederationScop, out: list
  `backend/app/api/v1/endpoints/admin.py`
- `GET` `/audit` → in: FederationScop, out: list
  `backend/app/api/v1/endpoints/admin.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/admin.py`

---
_Back to [overview.md](./overview.md)_