# Auth

> **Navigation aid.** Route list and file locations extracted via AST. Read the source files listed below before implementing or modifying this subsystem.

The Auth subsystem handles **5 routes** and touches: auth, db.

## Routes

- `GET` `/csrf` → out: CsrfResponse [auth]
  `backend/app/api/v1/endpoints/auth.py`
- `POST` `/login` → in: LoginRequest, out: CsrfResponse [auth, db]
  `backend/app/api/v1/endpoints/auth.py`
- `POST` `/logout` → in: LoginRequest, out: CsrfResponse [auth, db]
  `backend/app/api/v1/endpoints/auth.py`
- `POST` `/auth` → in: ProvisionDeviceRequest, out: ProvisionDeviceResponse [auth, db]
  `backend/app/api/v1/endpoints/devices.py`
- `POST` `/verify` → out: MfaSetupResponse [auth, db]
  `backend/app/api/v1/endpoints/mfa.py`

## Middleware

- **csrf** (auth) — `backend/app/api/middleware/csrf.py`
- **request_logging** (auth) — `backend/app/api/middleware/request_logging.py`
- **test_rate_limit** (auth) — `backend/tests/api/test_rate_limit.py`
- **auth** (auth) — `frontend/e2e/tests/helpers/auth.ts`

## Source Files

Read these before implementing or modifying this subsystem:
- `backend/app/api/v1/endpoints/auth.py`
- `backend/app/api/v1/endpoints/devices.py`
- `backend/app/api/v1/endpoints/mfa.py`

---
_Back to [overview.md](./overview.md)_