# Access

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Access subsystem handles **5 routes** and touches: auth.

## Routes

- `POST` `/qr/issue` → in: IssueQrRequest, out: IssueQrResponse [auth]
  `backend/app/api/v1/endpoints/access.py`
- `POST` `/qr/issue-self` → in: IssueQrRequest, out: IssueQrResponse [auth]
  `backend/app/api/v1/endpoints/access.py`
- `POST` `/qr/validate` → in: IssueQrRequest, out: IssueQrResponse [auth]
  `backend/app/api/v1/endpoints/access.py`
- `POST` `/keys/rotate` → in: IssueQrRequest, out: IssueQrResponse
  `backend/app/api/v1/endpoints/access.py`
- `GET` `/keys` → in: UUI, out: IssueQrResponse
  `backend/app/api/v1/endpoints/access.py`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/access.py`

---
_Back to [overview.md](./overview.md)_