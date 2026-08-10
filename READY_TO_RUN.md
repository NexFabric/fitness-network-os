# Uygulama hazır — çalıştırma özeti

**Tarih:** 2026-08-10  
**main equality:** `7671c25` — verify `git rev-parse HEAD` == `origin/main` after pull  
**Alembic head:** `q0d1e2f3a4b5`  
**Production-ready?** **NO** — Phase 26 CORE MVP EXIT GATE not passed.  
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

Admin Web uses **email/password** via `POST /api/v1/auth/login` (returns `token`, `user_id`, `expires_at`, `tenant_id`). Seed still prints a bearer token for API curl fallback.

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
| `bearer_token` | Admin → **Session token** (no `Bearer ` prefix) |
| `tenant_id` | Admin → **Tenant ID** |
| `email` / `password` | Admin login form → `POST /api/v1/auth/login` |

Default demo:

- email: `demo.admin@demo.local`
- password: `DemoAdmin123!`
- role: `GYM_OWNER`
- sample member `DEMO-001` + location `Demo Main Floor`

After login: Admin → **Members** (create member) and **Locations** (create location) against live APIs.

Re-run rotates the session token (prior sessions revoked).

### Password login (preferred)

```bash
curl -sS -X POST http://localhost:8000/api/v1/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"demo.admin@demo.local","password":"DemoAdmin123!"}'
```

Use returned `token` as Bearer and `tenant_id` as `X-Tenant-ID`.

Quick API check after seed:

```bash
curl -sS \
  -H "Authorization: Bearer <bearer_token>" \
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
npm run dev -- --port 5174
```

## API surface notes

- Public generic `/outbox` inject **yok** (15.5C — correct).
- Self: `/api/v1/me/*`, `/api/v1/access/qr/issue-self`
- Staff: members, locations, notifications, reports, finance, access, …
- Auth: HttpOnly cookie preferred; Bearer header accepted for local/admin MVP.
- Email notifications: `NOTIFICATION_EMAIL_PROVIDER=console` (default) or `log` — no real SMTP yet.

## Production-ready?

**Hayır.** MVP dev stack on main (~82–87% roadmap surface). Remaining production bar is tracked in:

- `docs/PROGRESS_CHECKLIST.md`
- `backend/docs/plans/REMAINING_WORK_BOARD.md`
- `backend/docs/plans/phase26_core_mvp_exit_gate.md`
- `frontend/UI_BRAND_SYSTEM.md`
