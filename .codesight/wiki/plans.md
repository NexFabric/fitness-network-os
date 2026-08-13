# Plans

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Plans subsystem handles **3 routes**.

## Routes

- `POST` `/{plan_id}/versions` params(plan_id) → in: PlanCreate, out: PlanResponse
  `backend/app/api/v1/endpoints/plans.py`
- `GET` `/versions` → in: UUI, out: PlanResponse
  `backend/app/api/v1/endpoints/plans.py`
- `POST` `/versions/{plan_version_id}/publish` params(plan_version_id) → in: PlanCreate, out: PlanResponse
  `backend/app/api/v1/endpoints/plans.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/plans.py`

---
_Back to [overview.md](./overview.md)_