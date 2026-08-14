# Infra

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Infra subsystem handles **6 routes** and touches: auth, db, cache.

## Routes

- `GET` `/` → in: UUI, out: ProvisionDeviceResponse [auth, db]
  `backend/app/api/v1/endpoints/devices.py`
- `GET` `/health` [auth, db, cache]
  `backend/app/main.py`
- `GET` `/live`
  `backend/app/main.py`
- `GET` `/ready` [auth, db, cache]
  `backend/app/main.py`
- `GET` `/metrics` [auth]
  `backend/app/main.py`
- `GET` `/ping`
  `backend/tests/core/test_security_headers.py`

## High-Impact Files

- `backend/app/main.py` — imported by 19 files

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/devices.py`
- `backend/app/main.py`
- `backend/tests/core/test_security_headers.py`

---
_Back to [overview.md](./overview.md)_