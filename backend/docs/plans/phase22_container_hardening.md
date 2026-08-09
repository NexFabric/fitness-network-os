# Phase 22 — Production container hardening

**Status:** 🟠 **IMPLEMENTED on branch** (light MVP) — **not LOCKED**  
**Branch:** `feat/phase16-notifications-reports`  
**Do not claim:** production-ready

---

## Goal

Ship a production-oriented container sketch without breaking local/dev Docker Compose.

## Landed

| Item | Detail |
|------|--------|
| Dev image | `backend/Dockerfile` — unchanged; used by root `docker-compose.yml` (`--reload`, volume mount) |
| Prod sketch | `backend/Dockerfile.prod` — multi-stage, non-root `appuser` (uid 1000), no `--reload` |
| Builder stage | `uv pip install --system` from `pyproject.toml` only (no dev dependency group) |
| Runtime stage | Copies site-packages + app source; `USER appuser`; `ENVIRONMENT=production` |

## Build (prod)

```bash
docker build -f backend/Dockerfile.prod -t fitness-os-backend:prod ./backend
```

Runtime still requires env: `DATABASE_URL`, `MIGRATOR_DATABASE_URL`, `REDIS_URL`, and production CORS (`CORS_ORIGINS`, see Phase 23).

## Explicit non-goals (this light MVP)

- No root compose prod profile / k8s manifests
- No distroless / scratch base, no image signing, no SBOM CI gate
- No secrets in image; no baked `.env`
- No healthcheck `HEALTHCHECK` instruction (optional later)
- No frontend multi-stage changes in this phase

## Do not break

- `docker-compose.yml` continues: `dockerfile: Dockerfile` under `./backend`
- Dev workflow: volume `./backend:/app` + uvicorn `--reload` remains

## Verify

```bash
# Dev (unchanged)
docker compose build backend

# Prod sketch
docker build -f backend/Dockerfile.prod -t fitness-os-backend:prod ./backend
```
