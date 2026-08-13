# Config

## Environment Variables

- `ALLOW_DESTRUCTIVE_TEST_RESET` **required** — backend/tests/conftest.py
- `ALLOW_MOCK_EMAIL` **required** — backend/app/services/notification_providers.py
- `ALLOW_MOCK_SMS_WA_PUSH` **required** — backend/app/services/notification_providers.py
- `CI` **required** — frontend/e2e/playwright.config.ts
- `DATABASE_URL` (has default) — backend/.env.example
- `ENCRYPTION_KEY` **required** — backend/app/core/security.py
- `ENVIRONMENT` **required** — backend/app/core/security.py
- `MIGRATOR_DATABASE_URL` (has default) — backend/.env.example
- `NEXT_PUBLIC_ADMIN_URL` **required** — frontend/public-site/src/components/Cta.tsx
- `QR_KMS_MODE` (has default) — backend/app/core/qr_crypto.py
- `REDIS_URL` (has default) — backend/.env.example
- `REPORT_STORAGE_DIR` (has default) — backend/app/services/report.py
- `S3_BUCKET_NAME` **required** — backend/app/services/storage.py
- `S3_ENDPOINT_URL` **required** — backend/app/services/storage.py
- `SMTP_FROM` (has default) — backend/app/services/notification_providers.py
- `SMTP_HOST` **required** — backend/app/services/notification_providers.py
- `SMTP_PASS` **required** — backend/app/services/notification_providers.py
- `SMTP_PORT` (has default) — backend/app/services/notification_providers.py
- `SMTP_USER` **required** — backend/app/services/notification_providers.py
- `TEST_DATABASE_URL` **required** — backend/scripts/check_permissions_db.py
- `TEST_RUNTIME_DATABASE_URL` (has default) — backend/tests/conftest.py
- `VITE_API_URL` (has default) — frontend/scanner-pwa/.env
- `VITE_SCANNER_URL` (has default) — frontend/admin-web/src/pages/PortalHome.tsx

## Config Files

- `backend/.env.example`
- `docker-compose.yml`
- `frontend/admin-web/tailwind.config.js`
- `frontend/admin-web/vite.config.ts`
- `frontend/public-site/next.config.ts`
- `frontend/scanner-pwa/tailwind.config.js`
- `frontend/scanner-pwa/vite.config.ts`
