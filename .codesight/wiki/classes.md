# Classes

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Classes subsystem handles **16 routes** and touches: auth, db.

## Routes

- `GET` `/trainers` → in: AsyncSessio, out: list
  `backend/app/api/v1/endpoints/classes.py`
- `GET` `/types` → in: AsyncSessio, out: list
  `backend/app/api/v1/endpoints/classes.py`
- `POST` `/types` → in: ClassTypeCreate, out: list
  `backend/app/api/v1/endpoints/classes.py`
- `PUT` `/types/{class_type_id}` params(class_type_id) → in: UUID, out: list
  `backend/app/api/v1/endpoints/classes.py`
- `GET` `/schedules` → in: AsyncSessio, out: list
  `backend/app/api/v1/endpoints/classes.py`
- `POST` `/schedules` → in: ClassTypeCreate, out: list
  `backend/app/api/v1/endpoints/classes.py`
- `PUT` `/schedules/{schedule_id}` params(schedule_id) → in: UUID, out: list
  `backend/app/api/v1/endpoints/classes.py`
- `POST` `/schedules/{schedule_id}/generate-sessions` params(schedule_id) → in: ClassTypeCreate, out: list [auth]
  `backend/app/api/v1/endpoints/classes.py`
- `GET` `/sessions/{session_id}/roster` params(session_id) → in: AsyncSessio, out: list [auth]
  `backend/app/api/v1/endpoints/classes.py`
- `POST` `/bookings/{booking_id}/attend` params(booking_id) → in: ClassTypeCreate, out: list [auth, db]
  `backend/app/api/v1/endpoints/classes.py`
- `POST` `/bookings/{booking_id}/cancel` params(booking_id) → in: ClassTypeCreate, out: list
  `backend/app/api/v1/endpoints/classes.py`
- `GET` `/trainers/availability` → in: AsyncSessio, out: list
  `backend/app/api/v1/endpoints/classes.py`
- `POST` `/trainers/availability` → in: ClassTypeCreate, out: list
  `backend/app/api/v1/endpoints/classes.py`
- `GET` `/pt/appointments` → in: AsyncSessio, out: list
  `backend/app/api/v1/endpoints/classes.py`
- `POST` `/pt/appointments` → in: ClassTypeCreate, out: list
  `backend/app/api/v1/endpoints/classes.py`
- `POST` `/pt/appointments/{appointment_id}/cancel` params(appointment_id) → in: ClassTypeCreate, out: list [db]
  `backend/app/api/v1/endpoints/classes.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/classes.py`

---
_Back to [overview.md](./overview.md)_