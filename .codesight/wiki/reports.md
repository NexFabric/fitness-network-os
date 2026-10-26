# Reports

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Reports subsystem handles **6 routes**.

## Routes

- `POST` `/definitions` → in: DefinitionCreate, out: DefinitionResponse
  `backend/app/api/v1/endpoints/reports.py`
- `GET` `/definitions` → in: UUI, out: DefinitionResponse
  `backend/app/api/v1/endpoints/reports.py`
- `POST` `/runs` → in: DefinitionCreate, out: DefinitionResponse
  `backend/app/api/v1/endpoints/reports.py`
- `GET` `/runs` → in: UUI, out: DefinitionResponse
  `backend/app/api/v1/endpoints/reports.py`
- `GET` `/runs/{run_id}` params(run_id) → in: UUI, out: DefinitionResponse
  `backend/app/api/v1/endpoints/reports.py`
- `POST` `/artifacts/cleanup` → in: DefinitionCreate, out: DefinitionResponse
  `backend/app/api/v1/endpoints/reports.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/reports.py`

---
_Back to [overview.md](./overview.md)_