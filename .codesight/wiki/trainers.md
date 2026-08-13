# Trainers

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Trainers subsystem handles **3 routes** and touches: auth, db.

## Routes

- `GET` `/{trainer_user_id}/members` params(trainer_user_id) → in: UUID, out: list [auth]
  `backend/app/api/v1/endpoints/trainers.py`
- `POST` `/{trainer_user_id}/members` params(trainer_user_id) → in: UUID, out: list [auth]
  `backend/app/api/v1/endpoints/trainers.py`
- `DELETE` `/{trainer_user_id}/members/{member_id}` params(trainer_user_id, member_id) → in: UUID, out: list [auth, db]
  `backend/app/api/v1/endpoints/trainers.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/trainers.py`

---
_Back to [overview.md](./overview.md)_