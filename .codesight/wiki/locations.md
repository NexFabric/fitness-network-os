# Locations

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Locations subsystem handles **4 routes**.

## Routes

- `POST` `` → in: LocationCreate, out: LocationResponse
  `backend/app/api/v1/endpoints/locations.py`
- `GET` `` → in: UUI, out: LocationResponse
  `backend/app/api/v1/endpoints/locations.py`
- `GET` `/{location_id}` params(location_id) → in: UUI, out: LocationResponse
  `backend/app/api/v1/endpoints/locations.py`
- `PATCH` `/{location_id}` params(location_id) → in: UUID, out: LocationResponse
  `backend/app/api/v1/endpoints/locations.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/locations.py`

---
_Back to [overview.md](./overview.md)_