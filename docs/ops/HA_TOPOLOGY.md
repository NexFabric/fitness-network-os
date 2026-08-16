# HA / topology contract

**Status:** **DOCUMENTED · NOT VERIFIED ON A LIVE HOST**

`docker-compose.prod.yml` is a **single-replica reference**:

- 1 backend
- 1 worker per type
- 1 admin-web, 1 scanner-pwa
- published ports `8000` / `8080` / `8081` (TLS termination is **not**
  in this file)

That is enough to run the application. It is **not** a production HA
topology.

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
| Object storage | real AWS S3 + SSE-KMS (`docs/ops/S3_RUNTIME_PROOF.md`) |
| Pager | Alertmanager `url_file` from a secret |

This project will not add Kubernetes, Kafka, or a second database to
satisfy this table. Those are platform choices.

## What compose already does

- migrate-before-app
- process `restart` policies
- `/live` healthcheck on the backend image
