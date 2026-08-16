# Production deploy and transport policy

**Status:** **IN-REPO GATE LANDED · LIVE DEPLOY NOT VERIFIED**

## Migration gate

`docker-compose.prod.yml` starts a one-shot `migrate` service
(`alembic upgrade head`) and will not start `backend` or workers until
that container exits 0.

Equivalent outside compose:

```bash
ops/deploy/migrate.sh
# only then
ops/deploy/smoke.sh
```

A failed migrate is a failed deploy.

## Transport encryption

`Settings.validate_production()` requires one of:

- `DATABASE_URL` query `sslmode=require` or `sslmode=verify-full`, and
  `REDIS_URL` scheme `rediss://`
- **or** `PRODUCTION_PRIVATE_NETWORK=1` — operator attestation that
  both endpoints are on a private network (VPC / RFC1918) and are not
  reachable from the public internet.

Public plaintext Postgres/Redis is a boot failure.

The application passes `ssl=True` (require) or a default SSL context
(verify-full) to asyncpg when the DSN asks for TLS.

## CORS

Every production `CORS_ORIGINS` entry must start with `https://`.
`http://` origins fail closed.

## Health

| Path | Meaning |
|---|---|
| `/live` | process up |
| `/ready` | Postgres + Redis reachable |
| `/health` | same checks as JSON |

## Still open

A real staging/production host, GitHub `production` environment
secrets, and a recorded rollback rehearsal.
