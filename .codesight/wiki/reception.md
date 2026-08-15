# Reception

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Reception subsystem handles **3 routes** and touches: auth, db.

## Routes

- `GET` `/search` → in: Annotated, out: list [auth, db]
  `backend/app/api/v1/endpoints/reception.py`
- `GET` `/member/{member_id}` params(member_id) → in: Annotated, out: list [auth, db]
  `backend/app/api/v1/endpoints/reception.py`
- `POST` `/checkin/{member_id}/override` params(member_id) → in: UUID, out: list [auth]
  `backend/app/api/v1/endpoints/reception.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/reception.py`

---
_Back to [overview.md](./overview.md)_