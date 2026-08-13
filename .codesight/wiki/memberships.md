# Memberships

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Memberships subsystem handles **6 routes** and touches: auth.

## Routes

- `POST` `/{membership_id}/freeze` params(membership_id) → in: UUID, out: MembershipFreezeResponse [auth]
  `backend/app/api/v1/endpoints/memberships.py`
- `POST` `/{membership_id}/unfreeze` params(membership_id) → in: UUID, out: MembershipFreezeResponse [auth]
  `backend/app/api/v1/endpoints/memberships.py`
- `POST` `/{membership_id}/cancel` params(membership_id) → in: UUID, out: MembershipFreezeResponse [auth]
  `backend/app/api/v1/endpoints/memberships.py`
- `POST` `/{membership_id}/renew` params(membership_id) → in: UUID, out: MembershipFreezeResponse [auth]
  `backend/app/api/v1/endpoints/memberships.py`
- `POST` `/{membership_id}/expire` params(membership_id) → in: UUID, out: MembershipFreezeResponse [auth]
  `backend/app/api/v1/endpoints/memberships.py`
- `POST` `/{membership_id}/past-due` params(membership_id) → in: UUID, out: MembershipFreezeResponse [auth]
  `backend/app/api/v1/endpoints/memberships.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/memberships.py`

---
_Back to [overview.md](./overview.md)_