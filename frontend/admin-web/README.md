# GymClubNex Admin Web (Phase 19 MVP)

Vite + React + TypeScript + Tailwind admin shell for staff.

## Scripts

| Script | Description |
|--------|-------------|
| `npm run dev` | Dev server (port 3000) |
| `npm run build` | Typecheck (`tsc`) + production build |
| `npm run preview` | Preview production build |

## Environment

Copy values into a local `.env` (never commit secrets):

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_URL` | No | API base URL. Default: `http://localhost:8000` |

Example `.env`:

```bash
VITE_API_URL=http://localhost:8000
```

## Auth (MVP)

There is no public login API yet. On **Login**, staff paste:

1. **Session token** — sent as `Authorization: Bearer <token>`
2. **Tenant ID** — sent as `X-Tenant-ID` (Gym = Tenant)

Both are stored in `localStorage` keys `fnos_access_token` and `fnos_tenant_id`.

## Pages

- `/login` — store token + tenant
- `/` — dashboard
- `/members` — `GET /api/v1/members`
- `/locations` — `GET /api/v1/locations`

## Docker

```bash
docker build -t gymclubnex-admin-web .
```

Build-time API URL can be injected via Docker `ARG`/`ENV` if needed; default client falls back to `http://localhost:8000`.
