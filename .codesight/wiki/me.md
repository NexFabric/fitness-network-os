# Me

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Me subsystem handles **7 routes** and touches: auth, db.

## Routes

- `GET` `/session` → in: AsyncSessio, out: MeSessionResponse [auth]
  `backend/app/api/v1/endpoints/me.py`
- `GET` `/profile` → in: AsyncSessio, out: MeSessionResponse [auth]
  `backend/app/api/v1/endpoints/me.py`
- `GET` `/member` → in: AsyncSessio, out: MeSessionResponse [auth]
  `backend/app/api/v1/endpoints/me.py`
- `GET` `/memberships` → in: AsyncSessio, out: MeSessionResponse [auth]
  `backend/app/api/v1/endpoints/me.py`
- `GET` `/entitlements` → in: AsyncSessio, out: MeSessionResponse [auth]
  `backend/app/api/v1/endpoints/me.py`
- `GET` `/checkins` → in: AsyncSessio, out: MeSessionResponse [auth, db]
  `backend/app/api/v1/endpoints/me.py`
- `POST` `/entitlements/check` → in: MeEntitlementCheckRequest, out: MeSessionResponse [auth]
  `backend/app/api/v1/endpoints/me.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/me.py`

---
_Back to [overview.md](./overview.md)_