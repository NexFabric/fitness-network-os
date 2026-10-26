# GymClubNex — Overview

> **Navigation aid.** This article shows WHERE things live (routes, models, files). Read actual source files before implementing new features or making changes.

**GymClubNex** is a python project built with fastapi, using sqlalchemy for data persistence, organized as a microservices repo.

**Services:** `backend` (`backend`), `fitness-network-os-frontend` (`frontend`), `admin-web` (`frontend/admin-web`), `gymclubnex-e2e` (`frontend/e2e`), `public-site` (`frontend/public-site`), `scanner-pwa` (`frontend/scanner-pwa`)

## Scale

142 API routes · 86 database models · 64 UI components · 83 library files · 6 middleware layers · 34 environment variables

## Subsystems

- **[Auth](./auth.md)** — 7 routes — touches: auth, db
- **[Access](./access.md)** — 5 routes — touches: auth
- **[Admin](./admin.md)** — 17 routes — touches: auth, db
- **[Break_glass](./break_glass.md)** — 3 routes — touches: auth, db
- **[Classes](./classes.md)** — 16 routes — touches: auth, db
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

**Libraries:** 83 files — see [libraries.md](./libraries.md)

## High-Impact Files

Changes to these files have the widest blast radius across the codebase:

- `backend/app/models/user.py` — imported by **75** files
- `backend/app/models/tenant.py` — imported by **69** files
- `backend/app/models/organization.py` — imported by **62** files
- `backend/app/api/deps.py` — imported by **47** files
- `backend/app/models/member.py` — imported by **47** files
- `backend/app/models/rbac.py` — imported by **45** files

## Required Environment Variables

- `ALLOW_DESTRUCTIVE_TEST_RESET` — `backend/tests/conftest.py`
- `AWS_KMS_KEY_ID` — `backend/app/core/qr_crypto.py`
- `CI` — `frontend/e2e/playwright.config.ts`
- `ENVIRONMENT` — `backend/app/core/security.py`
- `FITNESS_OS_TLS_SMOKE` — `backend/tests/test_asyncpg_tls_smoke.py`
- `METRICS_PORT` — `backend/app/core/metrics.py`
- `NEXT_PUBLIC_ADMIN_URL` — `frontend/public-site/src/components/Cta.tsx`
- `S3_BUCKET_NAME` — `backend/scripts/kms_iam_verify.py`
- `S3_ENDPOINT_URL` — `backend/scripts/s3_runtime_proof.py`
- `S3_KMS_KEY_ID` — `backend/scripts/kms_iam_verify.py`
- `SMTP_CA_BUNDLE` — `backend/app/services/notification_providers.py`
- `SMTP_PASS` — `backend/app/services/notification_providers.py`
- _...2 more_

---
_Back to [index.md](./index.md) · Generated 2026-08-16_