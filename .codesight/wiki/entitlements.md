# Entitlements

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Entitlements subsystem handles **2 routes** and touches: auth.

## Routes

- `POST` `/{member_id}/entitlements/check` params(member_id) → in: UUID, out: EntitlementAccessResponse [auth]
  `backend/app/api/v1/endpoints/entitlements.py`
- `POST` `/{member_id}/entitlements/consume` params(member_id) → in: UUID, out: EntitlementAccessResponse [auth]
  `backend/app/api/v1/endpoints/entitlements.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/entitlements.py`

---
_Back to [overview.md](./overview.md)_