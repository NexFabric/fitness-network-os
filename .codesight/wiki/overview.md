# GymClubNex — Overview

> **Navigation aid.** This article shows WHERE things live (routes, models, files). Read actual source files before implementing new features or making changes.

**GymClubNex** is a python project built with fastapi, using sqlalchemy for data persistence, organized as a microservices repo.

**Services:** `backend` (`backend`), `fitness-network-os-frontend` (`frontend`), `admin-web` (`frontend/admin-web`), `gymclubnex-e2e` (`frontend/e2e`), `public-site` (`frontend/public-site`), `scanner-pwa` (`frontend/scanner-pwa`)

## Scale

141 API routes · 86 database models · 64 UI components · 74 library files · 6 middleware layers · 19 environment variables

## Subsystems

- **[Auth](./auth.md)** — 7 routes — touches: auth, db
- **[Access](./access.md)** — 5 routes — touches: auth
- **[Admin](./admin.md)** — 17 routes — touches: auth, db
- **[Break_glass](./break_glass.md)** — 3 routes — touches: auth, db
- **[Classes](./classes.md)** — 15 routes — touches: auth, db
- **[Dashboard](./dashboard.md)** — 1 routes — touches: auth, db
- **[Data_import](./data_import.md)** — 4 routes — touches: auth, upload, db
- **[Devices](./devices.md)** — 2 routes — touches: auth, db
- **[Dsar_admin](./dsar_admin.md)** — 2 routes
- **[Entitlements](./entitlements.md)** — 2 routes — touches: auth
- **[Finance](./finance.md)** — 14 routes
- **[Locations](./locations.md)** — 3 routes
- **[Me](./me.md)** — 16 routes — touches: auth, db
- **[Members](./members.md)** — 11 routes — touches: cache, db
- **[Memberships](./memberships.md)** — 6 routes — touches: auth
- **[Mfa](./mfa.md)** — 2 routes — touches: db, cache, auth
- **[Notifications](./notifications.md)** — 5 routes — touches: db
- **[Onboarding](./onboarding.md)** — 1 routes — touches: auth, db
- **[Plans](./plans.md)** — 3 routes
- **[Reception](./reception.md)** — 3 routes — touches: auth, db
- **[Reports](./reports.md)** — 6 routes
- **[Staff](./staff.md)** — 2 routes — touches: auth, cache
- **[Telemetry](./telemetry.md)** — 1 routes
- **[Trainers](./trainers.md)** — 3 routes — touches: auth, db
- **[Infra](./infra.md)** — 7 routes — touches: auth, db, cache

**Database:** sqlalchemy, 86 models — see [database.md](./database.md)

**UI:** 64 components (react) — see [ui.md](./ui.md)

**Libraries:** 74 files — see [libraries.md](./libraries.md)

## High-Impact Files

Changes to these files have the widest blast radius across the codebase:

- `backend/app/models/user.py` — imported by **67** files
- `backend/app/models/tenant.py` — imported by **59** files
- `backend/app/models/organization.py` — imported by **52** files
- `backend/app/api/deps.py` — imported by **47** files
- `backend/app/models/member.py` — imported by **41** files
- `backend/app/models/rbac.py` — imported by **40** files

## Required Environment Variables

- `ALLOW_DESTRUCTIVE_TEST_RESET` — `backend/tests/conftest.py`
- `AWS_KMS_KEY_ID` — `backend/app/core/qr_crypto.py`
- `CI` — `frontend/e2e/playwright.config.ts`
- `ENVIRONMENT` — `backend/app/core/security.py`
- `NEXT_PUBLIC_ADMIN_URL` — `frontend/public-site/src/components/Cta.tsx`
- `SMTP_PASS` — `backend/app/services/notification_providers.py`
- `SMTP_USER` — `backend/app/services/notification_providers.py`
- `TEST_DATABASE_URL` — `backend/scripts/check_permissions_db.py`

---
_Back to [index.md](./index.md) · Generated 2026-08-16_