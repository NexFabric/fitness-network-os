# HA / topology contract

**Status:** **UNVERIFIED** · live host

Index: `docs/ops/EXTERNAL_GATES.md`. `docker-compose.prod.yml` is a
**single-replica reference**. That is enough to run the application. It
is **not** a production HA topology.

## Close this gate (one command)

Owner: **A-OPS**. Point at a live HTTPS API, then attest the platform
facts the compose file cannot see.

```bash
export SMOKE_BASE_URL=https://api.example.com
export BACKEND_REPLICA_EVIDENCE=$HOME/fitness-os-ha-replicas.txt
export MULTI_AZ_EVIDENCE=$HOME/fitness-os-ha-multiaz.txt
# Each evidence file is operator-captured output (kubectl get / aws elbv2 /
# aws rds describe / docker compose ps). Not a comment.
./ops/ha/live_check.sh
```

`ops/deploy/smoke.sh` alone proves `/live` and `/ready`. This gate also
requires replica and multi-AZ evidence files. Exit 2 = `NOT VERIFIED`.

## Platform contract (outside this repo)

A public production deployment must supply:

| Concern | Expected outside compose |
|---|---|
| Ingress / TLS | Edge or reverse proxy; HTTPS only; HSTS at the edge |
| WAF / DDoS | Cloud/edge, not the FastAPI process |
| Backend replicas | ≥2 behind a load balancer; `/ready` for membership |
| Workers | at least one replica per queue; outbox uses `SKIP LOCKED` |
| PostgreSQL | managed multi-AZ + continuous off-host WAL (`docs/ops/WAL_ARCHIVE.md`) |
| Redis | managed HA or private TLS (`rediss://`) |
| Object storage | real AWS S3 + SSE-KMS (`ops/s3/README.md`) |
| Pager | Alertmanager `url_file` from a secret (`ops/observability/pager_prove.sh`) |

This project will not add Kubernetes, Kafka, or a second database to
satisfy this table. Those are platform choices.

## What compose already does

- migrate-before-app
- process `restart` policies
- `/live` healthcheck on the backend image

`docker-compose.prod.yml` publishes `8000` / `8080` / `8081`. TLS
termination is **not** in that file. One backend container is **not**
HA even if `restart: always` is set.

## Live facts (empty until a host exists)

| Fact | Value |
|---|---|
| API origin | |
| Backend replica count | |
| Worker replica count (outbox / notification / report / retention) | |
| Postgres | managed multi-AZ / not |
| Redis | managed HA / `rediss://` / not |
| Edge TLS + HSTS | |
| Last `live_check.sh` log | |

Do not fill this table from a laptop compose stack.

## Evidence log

| Date | Host | Command | Result |
|---|---|---|---|
| — | — | — | **Never run against a live production host.** |
