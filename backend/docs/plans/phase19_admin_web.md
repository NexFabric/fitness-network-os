# Phase 19 — Admin Web MVP

**Status:** 🟠 **IMPLEMENTED on branch** — **not LOCKED**  
**Path:** `frontend/admin-web/`  
**Branch:** `feat/phase16-notifications-reports`  
**Do not claim:** production-ready

---

## Goal

Ship a minimal staff admin shell that can talk to the real API V1 surface with tenant context.

## Landed

| Item | Detail |
|------|--------|
| Stack | Vite + React + TypeScript + Tailwind + React Router |
| Login | Paste session Bearer + Tenant UUID → `localStorage` (`fnos_access_token`, `fnos_tenant_id`) |
| Shell | Dashboard, Layout nav, RequireAuth gate |
| Members | `GET /api/v1/members` via `VITE_API_URL` |
| Locations | `GET /api/v1/locations` |
| API client | `Authorization: Bearer` + `X-Tenant-ID` |
| Docker | `Dockerfile` (node build → nginx) |
| README | `frontend/admin-web/README.md` |

## Gaps / next

- No public login API / cookie session UI yet (deps token paste)
- No create/edit flows, finance, memberships lifecycle UI
- Lint script references eslint without package (use `build` as gate)
- No CI job for frontend build yet (Phase 21)

## Verify

```bash
cd frontend/admin-web
npm install
VITE_API_URL=http://localhost:8000 npm run build
npm run dev
```
