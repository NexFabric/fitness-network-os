# Uygulama hazır — çalıştırma özeti

**Tarih:** 2026-08-13
**Main:** `2a1002d` — final closure PR #55 merge edildi, açık PR yok.
**Alembic head:** `v5c6d7e8f9a0`.
**Production-ready?** **NO** — kod kapıları kapandı; restore/PITR tatbikatı, gerçek S3 staging kanıtı ve bağımsız pentest açık.
**UI brand:** Admin teal staff console + Scanner “GymClubNex · Access” (`frontend/UI_BRAND_SYSTEM.md`).

## Servis URL’leri

| Servis | URL | Not |
|--------|-----|-----|
| API health | http://localhost:8000/health | docker `backend` |
| API Swagger | http://localhost:8000/docs | OpenAPI |
| Admin Web | http://localhost:5173/ | Vite; login: http://localhost:5173/login (branded) |
| Scanner PWA | http://localhost:5174/ | camera QR or paste → GRANT/DENY (Access brand) |
| Postgres | localhost:**5433** | mapped from container 5432 |
| Redis | localhost:6379 | docker |

## 1) Infra + migrate

```bash
cd /Users/emrah/GymClubNex
docker compose up -d

cd backend
set -a && source .env && set +a
# use project venv / uv as available
alembic upgrade head
```

`.env` (local host ports):

```text
DATABASE_URL=postgresql+asyncpg://fitness_app:fitness_app_password@localhost:5433/fitness_os
MIGRATOR_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/fitness_os
REDIS_URL=redis://localhost:6379/0
```

If role `fitness_app` is missing (volume predates `postgres-init.sql`), create it once:

```bash
PGPASSWORD=postgres psql -h localhost -p 5433 -U postgres -d fitness_os -f ../postgres-init.sql
# plus grants on existing tables if volume already had schema
```

## 2) Demo seed (Admin login credentials)

Admin Web uses **email/password** via `POST /api/v1/auth/login` (sets HttpOnly cookie, returns `{"status": "ok"}`).  
CSRF tokens are required via `GET /api/v1/auth/csrf`. Seed prints test credentials.
```bash
cd backend
set -a && source .env && set +a
uv run python scripts/seed_demo.py
# equivalent:
# uv run python scripts/seed_demo_tenant.py
```

Script prints (example fields):

| Field | Use |
|-------|-----|
| `tenant_id` | Admin → **Tenant ID** |
| `email` / `password` | Admin login form → `POST /api/v1/auth/login` |

Default demo:

- email: `demo.admin@demo.local`
- password: `DemoAdmin123!`
- role: `GYM_OWNER`
- sample member `DEMO-001` + location `Demo Main Floor`

After login: Admin → **Members** (create member) and **Locations** (create location) against live APIs.

Re-run rotates the session token (prior sessions revoked).

### Role matrix seed (one login per portal)

`seed_demo.py` only creates a `GYM_OWNER`. To exercise all five portals — and the
trainer assignment scope — seed one principal per role in a shared tenant:

```bash
cd backend
uv run python scripts/seed_role_matrix.py   # idempotent; prints credentials as JSON
```

| Email | Role | Lands on |
|-------|------|----------|
| `e2e.owner@e2e.local` | `GYM_OWNER` | ops console |
| `e2e.trainer@e2e.local` | `TRAINER` | trainer portal (assigned members only) |
| `e2e.member@e2e.local` | `MEMBER` | athlete portal |
| `e2e.analyst@e2e.local` | `FEDERATION_ANALYST` | federation console |

Password for all four: `E2ePortal123!` (local fixture, never a real secret).
Routing after login is role-based, and cross-portal URLs are denied by
`RequireRole` — see `docs/RBAC.md`. This seed also backs the Playwright suite:

```bash
cd frontend/e2e && npx playwright test    # 21 tests, starts :5173/:5174 itself
```

### Password login (preferred API check)

```bash
# Get CSRF
curl -sS -c cookie.txt http://localhost:8000/api/v1/auth/csrf

# Login
curl -sS -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -H 'X-CSRF-Token: <token>' \
  -b cookie.txt -c cookie.txt \
  -d '{"email":"demo.admin@demo.local","password":"DemoAdmin123!"}'

# Check API
curl -sS \
  -b cookie.txt \
  -H "X-Tenant-ID: <tenant_id>" \
  http://localhost:8000/api/v1/members
```

## 3) Frontends

```bash
# Admin
cd frontend/admin-web
echo 'VITE_API_URL=http://localhost:8000' > .env
npm run dev -- --port 5173

# Scanner
cd frontend/scanner-pwa
echo 'VITE_API_URL=http://localhost:8000' > .env
npm run dev
```

### Pairing a scanner device (signed channel)

The device channel needs two things, not one: the `device_session` cookie **and**
the per-session signing secret. Provision as staff, then pair:

```bash
# 1) Staff provisions the device (needs devices:manage) — returns api_key ONCE
curl -sS -X POST http://localhost:8000/api/v1/devices/provision \
  -b cookie.txt -H 'Content-Type: application/json' \
  -H "X-Tenant-ID: <tenant_id>" \
  -d '{"name":"Turnike 1","location_id":"<location_id>"}'

# 2) The device authenticates — returns signing_secret ONCE (body, not a cookie)
curl -sS -X POST http://localhost:8000/api/v1/devices/auth \
  -H 'Content-Type: application/json' \
  -d '{"device_id":"<id>","tenant_id":"<tenant_id>","api_key":"<api_key>"}'
```

In the browser the scanner does this via `authenticateDevice()`
(`frontend/scanner-pwa/src/api/client.ts`), which imports the secret into a
non-extractable `CryptoKey` — the plaintext is never stored.

Every later device request must carry `X-Device-Timestamp`, `X-Device-Nonce` and
`X-Device-Signature` = HMAC-SHA256 over
`METHOD\npath\ntimestamp\nnonce\nsha256(body)`, within ±300s. A request without a
valid signature is 401 regardless of the cookie (ADR-044). Unpaired scanners keep
working through the staff path `/api/v1/access/qr/validate`.

## API surface notes

- Public generic `/outbox` inject **yok** (15.5C — correct).
- Self: `/api/v1/me/*`, `/api/v1/access/qr/issue-self`
- Staff: members, locations, notifications, reports, finance, access, …
- Auth: HttpOnly cookie + CSRF token enforcement.
- Device: HMAC-SHA256 request signing + single-use nonce (`ADR-044`).
- Email notifications: SMTP integration is active in `docker-compose.prod.yml`.

## Production-ready?

**Hayır.** MVP dev stack on main (~82–87% roadmap surface). Remaining production bar is tracked in:

- `docs/PROGRESS_CHECKLIST.md`
- `backend/docs/plans/REMAINING_WORK_BOARD.md`
- `backend/docs/plans/phase26_core_mvp_exit_gate.md`
- `frontend/UI_BRAND_SYSTEM.md`
