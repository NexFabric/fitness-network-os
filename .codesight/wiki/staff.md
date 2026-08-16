# Staff

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Staff subsystem handles **2 routes** and touches: auth, cache.

## Routes

- `POST` `/accounts` → in: StaffLinkRequest, out: StaffResponse [auth, cache]
  `backend/app/api/v1/endpoints/staff.py`
- `GET` `/{staff_id}` params(staff_id) → in: UUI, out: StaffResponse
  `backend/app/api/v1/endpoints/staff.py`

## Related Models

- **Staff** (3 fields) → [database.md](./database.md)

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/staff.py`

---
_Back to [overview.md](./overview.md)_