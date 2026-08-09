# Phase 23 — HTTP security baseline (CORS + headers)

**Status:** 🟠 **IMPLEMENTED on branch** (light MVP) — **not LOCKED**  
**Branch:** `feat/phase16-notifications-reports`  
**Do not claim:** production-ready

---

## Goal

Environment-aware CORS allowlist and basic browser security headers without breaking local permissive CORS.

## Landed

| Item | Detail |
|------|--------|
| Settings | `ENVIRONMENT` (default `local`), `CORS_ORIGINS` (comma-separated string) on `app.core.config.Settings` |
| Helpers | `Settings.is_production`, `Settings.cors_origins_list` |
| CORS | Production: origins from `CORS_ORIGINS` only; non-production: keep `allow_origins=["*"]` |
| Headers | Middleware: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` |
| Request id | See Phase 24 (`X-Request-ID`); out of scope for this plan |
| Tests | `tests/core/test_config_cors.py` — CORS list parsing + production flag |
| Env example | `.env.example` documents optional `ENVIRONMENT` / `CORS_ORIGINS` |

## Behavior

### Non-production (`ENVIRONMENT` ≠ `production`)

- CORS remains permissive: `allow_origins=["*"]`, all methods/headers (local/dev UX).
- Security headers still applied (safe for all environments).

### Production (`ENVIRONMENT=production`)

- `CORS_ORIGINS` is required for useful browser clients: comma-separated absolute origins  
  e.g. `https://admin.example.com,https://scanner.example.com`
- Empty / missing list → no allowed origins (fail closed for browser CORS).
- Methods: standard HTTP verbs + OPTIONS; credentials allowed when origins are explicit.

## Env

```bash
ENVIRONMENT=production
CORS_ORIGINS=https://admin.example.com,https://scanner.example.com
```

## Explicit non-goals (this light MVP)

- No HSTS / CSP / CSRF tokens (later Wave 0 / readiness track)
- No TrustedHostMiddleware allowlist
- No rate limiting or WAF
- No cookie `Secure`/`SameSite` policy changes (auth cookies not in this phase)

## Verify

```bash
cd backend
# unit (no DB required if only this module — still needs env for full suite)
uv run pytest tests/core/test_config_cors.py -q
```
