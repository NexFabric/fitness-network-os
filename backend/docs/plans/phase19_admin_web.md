# Phase 19 — Admin Web MVP

**Status:** 🟠 **MERGED on main** — **not LOCKED**  
**Path:** `frontend/admin-web/`  
**Main evidence:** PRs #26 stack + #37/#38 create flows + #45 brand  
**Do not claim:** production-ready

---

## Goal

Staff admin shell that talks to real API V1 with tenant context.

## Landed (main)

| Item | Detail |
|------|--------|
| Stack | Vite + React + TypeScript + Tailwind + React Router |
| Login | **Email/password** → `POST /api/v1/auth/login`; stores Bearer + tenant in localStorage |
| Brand | GymClubNex teal system (`UI_BRAND_SYSTEM.md`); DM Sans; branded login/shell/dashboard |
| Shell | Layout nav (Dashboard / Members / Locations), RequireAuth, tenant chip |
| Members | List + **create** (`POST /api/v1/members`) |
| Locations | List + **create** (`POST /api/v1/locations`) |
| Dashboard | Operations welcome + live list counts |
| API client | Bearer + `X-Tenant-ID` + `credentials: 'include'` |
| Docker | `Dockerfile` (node build → nginx) |
| CI | Admin Web Build job in `.github/workflows/ci.yml` |

## Gaps / next

- Cookie-only session (drop localStorage token)  
- Edit member / location; membership lifecycle; finance UI  
- Not LOCKED; not production-ready  

## Verify

```bash
cd frontend/admin-web
npm install
VITE_API_URL=http://localhost:8000 npm run build
npm run dev -- --port 5173
```
