# Notifications

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Notifications subsystem handles **5 routes** and touches: db.

## Routes

- `POST` `/templates` → in: TemplateCreate, out: TemplateResponse
  `backend/app/api/v1/endpoints/notifications.py`
- `GET` `/templates` → in: UUI, out: TemplateResponse
  `backend/app/api/v1/endpoints/notifications.py`
- `POST` `/deliveries` → in: TemplateCreate, out: TemplateResponse
  `backend/app/api/v1/endpoints/notifications.py`
- `GET` `/deliveries` → in: UUI, out: TemplateResponse
  `backend/app/api/v1/endpoints/notifications.py`
- `GET` `/deliveries/{delivery_id}` params(delivery_id) → in: UUI, out: TemplateResponse [db]
  `backend/app/api/v1/endpoints/notifications.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/notifications.py`

---
_Back to [overview.md](./overview.md)_