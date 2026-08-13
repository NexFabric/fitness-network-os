# Mfa

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Mfa subsystem handles **1 routes** and touches: db.

## Routes

- `POST` `/setup` → in: Use, out: MfaSetupResponse [db]
  `backend/app/api/v1/endpoints/mfa.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/mfa.py`

---
_Back to [overview.md](./overview.md)_