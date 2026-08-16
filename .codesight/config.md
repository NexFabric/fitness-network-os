# Config

## Environment Variables

- `ALLOW_DESTRUCTIVE_TEST_RESET` **required** — backend/tests/conftest.py
- `AWS_KMS_KEY_ID` **required** — backend/app/core/qr_crypto.py
- `CI` **required** — frontend/e2e/playwright.config.ts
- `DATABASE_URL` (has default) — backend/.env.example
- `E2E_API_URL` (has default) — frontend/e2e/tests/helpers/auth.ts
- `E2E_OWNER_TOTP_SECRET` (has default) — backend/scripts/seed_role_matrix.py
- `ENCRYPTION_KEY` (has default) — backend/.env.example
- `ENVIRONMENT` **required** — backend/app/core/security.py
- `MIGRATOR_DATABASE_URL` (has default) — backend/.env.example
- `MINIO_ROOT_PASSWORD` (has default) — backend/scripts/s3_runtime_proof.py
- `MINIO_ROOT_USER` (has default) — backend/scripts/s3_runtime_proof.py
- `NEXT_PUBLIC_ADMIN_URL` **required** — frontend/public-site/src/components/Cta.tsx
- `QR_KMS_MODE` (has default) — backend/app/core/qr_crypto.py
- `REDIS_URL` (has default) — backend/.env.example
- `S3_BUCKET_NAME` **required** — backend/scripts/kms_iam_verify.py
- `S3_ENDPOINT_URL` **required** — backend/scripts/s3_runtime_proof.py
- `S3_KMS_KEY_ID` **required** — backend/scripts/kms_iam_verify.py
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
