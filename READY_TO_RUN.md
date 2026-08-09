# Uygulama hazır — çalıştırma özeti

**Tarih:** 2026-08-10  
**main:** güncel · migration: `q0d1e2f3a4b5` (head)

## Servisler (şu an ayağa kalktı)

| Servis | URL | Durum |
|--------|-----|--------|
| API health | http://localhost:8000/health | ✅ |
| API Swagger | http://localhost:8000/docs | ✅ |
| Admin Web | http://localhost:5173/ | ✅ |
| Scanner PWA | http://localhost:5174/ | ✅ |
| Postgres | localhost:**5433** | ✅ docker |
| Redis | localhost:6379 | ✅ docker |

## Nasıl yeniden başlatılır

```bash
cd /Users/emrah/GymClubNex
docker compose up -d
cd backend && source .venv/bin/activate && set -a && source .env && set +a
alembic upgrade head

# Frontends (ayrı terminaller)
cd frontend/admin-web && echo 'VITE_API_URL=http://localhost:8000' > .env && npm run dev -- --port 5173
cd frontend/scanner-pwa && echo 'VITE_API_URL=http://localhost:8000' > .env && npm run dev -- --port 5174
```

## Admin / Scanner kullanımı

1. **Admin** (`5173`): Login ekranında session **Bearer token** + **X-Tenant-ID** (UUID) gerekir.  
   Token: demo seed (aşağıda) veya DB’de `user_sessions`.
2. **Scanner** (`5174`): QR token yapıştır → `POST /api/v1/access/qr/validate`.

## Demo seed (Admin login)

Idempotent script: Organization + Tenant + `GYM_ADMIN` user + session token + optional Member.

```bash
cd /Users/emrah/GymClubNex/backend
source .venv/bin/activate   # or: uv run …
set -a && source .env && set +a
alembic upgrade head
python scripts/seed_demo_tenant.py
```

Defaults (override with `--email` / `--password` / `--role GYM_OWNER` / `--no-member`):

| Field | Default |
|-------|---------|
| email | `demo.admin@demo.local` |
| password | `DemoAdmin123!` |
| role | `GYM_ADMIN` (permissions from DB matrix) |
| location_code | `DEMO-MAIN` |

Stdout prints `tenant_id` + raw `bearer_token` — paste both into Admin login (`5173`). Token is stored hashed in `user_sessions` (raw only shown once per run; re-run issues a new token and revokes prior open sessions for that user).

## API notları

- Public generic `/outbox` **yok** (doğru).
- Self: `/api/v1/me/*`, `/api/v1/access/qr/issue-self`
- Staff: members, locations, notifications, reports, finance, …

## Production-ready?

**Hayır** — MVP dev stack. Gerçek provider / full security ayrı.
