# Members

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Members subsystem handles **10 routes** and touches: db.

## Routes

- `GET` `/{member_id}` params(member_id) → out: MemberResponse
  `backend/app/api/v1/endpoints/members.py`
- `PATCH` `/{member_id}` params(member_id) → in: UUID, out: MemberResponse
  `backend/app/api/v1/endpoints/members.py`
- `POST` `/{member_id}/status` params(member_id) → in: MemberCreate, out: MemberResponse
  `backend/app/api/v1/endpoints/members.py`
- `POST` `/{member_id}/tags` params(member_id) → in: MemberCreate, out: MemberResponse
  `backend/app/api/v1/endpoints/members.py`
- `GET` `/{member_id}/tags` params(member_id) → out: MemberResponse
  `backend/app/api/v1/endpoints/members.py`
- `POST` `/{member_id}/notes` params(member_id) → in: MemberCreate, out: MemberResponse
  `backend/app/api/v1/endpoints/members.py`
- `GET` `/{member_id}/notes` params(member_id) → out: MemberResponse
  `backend/app/api/v1/endpoints/members.py`
- `POST` `/{member_id}/consents` params(member_id) → in: MemberCreate, out: MemberResponse
  `backend/app/api/v1/endpoints/members.py`
- `GET` `/{member_id}/memberships` params(member_id) → out: MemberResponse
  `backend/app/api/v1/endpoints/members.py`
- `GET` `/{member_id}/access-logs` params(member_id) → out: MemberResponse [db]
  `backend/app/api/v1/endpoints/members.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/members.py`

---
_Back to [overview.md](./overview.md)_