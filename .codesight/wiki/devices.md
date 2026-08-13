# Devices

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Devices subsystem handles **2 routes** and touches: auth, db.

## Routes

- `POST` `/provision` → in: ProvisionDeviceRequest, out: ProvisionDeviceResponse [auth]
  `backend/app/api/v1/endpoints/devices.py`
- `POST` `/revoke` → in: ProvisionDeviceRequest, out: ProvisionDeviceResponse [auth, db]
  `backend/app/api/v1/endpoints/devices.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/devices.py`

---
_Back to [overview.md](./overview.md)_