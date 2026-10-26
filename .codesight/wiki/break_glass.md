# Break_glass

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Break_glass subsystem handles **3 routes** and touches: auth, db.

## Routes

- `POST` `/sessions` → in: CreateBreakGlassRequest, out: BreakGlassSessionResponse [auth]
  `backend/app/api/v1/endpoints/break_glass.py`
- `GET` `/sessions` → in: AsyncSessio, out: BreakGlassSessionResponse [auth, db]
  `backend/app/api/v1/endpoints/break_glass.py`
- `POST` `/sessions/{session_id}/revoke` params(session_id) → in: CreateBreakGlassRequest, out: BreakGlassSessionResponse [auth]
  `backend/app/api/v1/endpoints/break_glass.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/break_glass.py`

---
_Back to [overview.md](./overview.md)_