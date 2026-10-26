# Onboarding

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Onboarding subsystem handles **1 routes** and touches: auth, db.

## Routes

- `POST` `/advance` → in: AdvanceStageRequest, out: OnboardingStatusResponse [auth, db]
  `backend/app/api/v1/endpoints/onboarding.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/onboarding.py`

---
_Back to [overview.md](./overview.md)_