# Dashboard

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Dashboard subsystem handles **1 routes** and touches: auth, db.

## Routes

- `GET` `/kpis` → in: AsyncSessio, out: DashboardKPIResponse [auth, db]
  `backend/app/api/v1/endpoints/dashboard.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/dashboard.py`

---
_Back to [overview.md](./overview.md)_