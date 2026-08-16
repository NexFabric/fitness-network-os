# Production deploy choreography

This repository does **not** own a cloud account. These scripts are the
in-repo contract for any platform that runs `docker-compose.prod.yml`
or an equivalent release command.

## Required order

1. **Migrate** — `ops/deploy/migrate.sh` / compose service `migrate`.
   Failure **aborts**. Do not start API or workers.
2. **Roll** backend, then workers. Frontends may follow once `/ready` is 200.
3. **Smoke** — `ops/deploy/smoke.sh` against `/live` and `/ready`.
4. **Abort / rollback** — see `rollback.md`. Never auto-downgrade schema.

`docker-compose.prod.yml` encodes step 1 as
`depends_on: migrate: condition: service_completed_successfully`.

## Transport

Production boot refuses plaintext Postgres/Redis unless the operator
sets `PRODUCTION_PRIVATE_NETWORK=1` (VPC-only attestation). Prefer
`sslmode=require` / `verify-full` and `rediss://`. See
`docs/ops/PRODUCTION_DEPLOY.md`.

## GitHub Actions

`.github/workflows/deploy.yml` is `workflow_dispatch` only. It builds
images and refuses to report success when the long-lived backend
secrets from `docker-compose.prod.yml` are absent:
`DATABASE_URL`, `REDIS_URL`, `ENCRYPTION_KEY`, `AWS_KMS_KEY_ID`,
`S3_BUCKET_NAME`, `METRICS_BEARER_TOKEN`, and `SMTP_*` when the
provider is `smtp` (compose default). `QR_KMS_MODE` defaults to
`aws_kms` and any other value is fail-closed. `MIGRATOR_DATABASE_URL`
is migrate-only and is **not** required on the promote job.
It does not invent an ECS/Kubernetes target.
