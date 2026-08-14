# GymClubNex — Overview

> **Navigation aid.** This article shows WHERE things live (routes, models, files). Read actual source files before implementing new features or making changes.

**GymClubNex** is a python project built with fastapi, using sqlalchemy for data persistence, organized as a microservices repo.

**Services:** `backend` (`backend`), `fitness-network-os-frontend` (`frontend`), `admin-web` (`frontend/admin-web`), `gymclubnex-e2e` (`frontend/e2e`), `public-site` (`frontend/public-site`), `scanner-pwa` (`frontend/scanner-pwa`)

## Scale

88 API routes · 73 database models · 38 UI components · 63 library files · 6 middleware layers · 17 environment variables

## Subsystems

- **[Auth](./auth.md)** — 6 routes — touches: auth, db
- **[Access](./access.md)** — 5 routes — touches: auth
- **[Admin](./admin.md)** — 5 routes
- **[Devices](./devices.md)** — 2 routes — touches: auth, db
- **[Entitlements](./entitlements.md)** — 2 routes — touches: auth
- **[Finance](./finance.md)** — 14 routes
- **[Locations](./locations.md)** — 4 routes
- **[Me](./me.md)** — 7 routes — touches: auth, db
- **[Members](./members.md)** — 10 routes — touches: db
- **[Memberships](./memberships.md)** — 6 routes — touches: auth
- **[Mfa](./mfa.md)** — 1 routes — touches: db, cache
- **[Notifications](./notifications.md)** — 5 routes — touches: db
- **[Plans](./plans.md)** — 3 routes
- **[Reports](./reports.md)** — 6 routes
- **[Staff](./staff.md)** — 2 routes — touches: cache
- **[Telemetry](./telemetry.md)** — 1 routes
- **[Trainers](./trainers.md)** — 3 routes — touches: auth, db
- **[Infra](./infra.md)** — 6 routes — touches: auth, db, cache

**Database:** sqlalchemy, 73 models — see [database.md](./database.md)

**UI:** 38 components (react) — see [ui.md](./ui.md)

**Libraries:** 63 files — see [libraries.md](./libraries.md)

## High-Impact Files

Changes to these files have the widest blast radius across the codebase:

- `backend/app/models/user.py` — imported by **45** files
- `backend/app/models/tenant.py` — imported by **43** files
- `backend/app/models/organization.py` — imported by **37** files
- `backend/app/db/base.py` — imported by **34** files
- `backend/app/api/deps.py` — imported by **32** files
- `backend/app/models/member.py` — imported by **30** files

## Required Environment Variables

- `ALLOW_DESTRUCTIVE_TEST_RESET` — `backend/tests/conftest.py`
- `CI` — `frontend/e2e/playwright.config.ts`
- `ENCRYPTION_KEY` — `backend/app/core/security.py`
- `ENVIRONMENT` — `backend/app/core/security.py`
- `NEXT_PUBLIC_ADMIN_URL` — `frontend/public-site/src/components/Cta.tsx`
- `SMTP_PASS` — `backend/app/services/notification_providers.py`
- `SMTP_USER` — `backend/app/services/notification_providers.py`
- `TEST_DATABASE_URL` — `backend/scripts/check_permissions_db.py`

---
_Back to [index.md](./index.md) · Generated 2026-08-14_