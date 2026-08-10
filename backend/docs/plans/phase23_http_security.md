# Phase 23 — HTTP security baseline (CORS + headers)

**Status:** 🟠 **PARTIAL (deeper)** — CORS allowlist + security headers + login rate limit  
**Branch (this slice):** `feat/http-security-headers`  
**Do not claim:** LOCKED, production-ready, full ASVS, or Wave-0 exit PASS

---

## Goal

Environment-aware CORS allowlist and browser security headers without breaking local permissive CORS / admin / scanner UX.

## Landed

| Item | Detail |
|------|--------|
| Settings | `ENVIRONMENT` (default `local`), `CORS_ORIGINS`, `ALLOWED_HOSTS` (comma-separated) on `app.core.config.Settings` |
| Helpers | `Settings.is_production`, `Settings.cors_origins_list`, `Settings.allowed_hosts_list` |
| CORS | Production: origins from `CORS_ORIGINS` only; non-production: keep `allow_origins=["*"]` |
| Headers (always) | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin` |
| Headers (production only) | `Strict-Transport-Security: max-age=31536000; includeSubDomains`, `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'; base-uri 'none'` (JSON API default) |
| TrustedHost | **Only** when `ENVIRONMENT=production` **and** `ALLOWED_HOSTS` non-empty; if unset, middleware is **not** installed (safe skip for local / unset prod hosts) |
| Rate limit | In-memory `SimpleRateLimitMiddleware` on `POST /api/v1/auth/login` (MVP; not multi-worker) — separate from this header slice |
| Request id | See Phase 24 (`X-Request-ID`); out of scope for this plan |
| Tests | `tests/core/test_config_cors.py`, `tests/core/test_security_headers.py`, `tests/test_health.py` (always-on headers) |
| Env example | `.env.example` documents optional `ENVIRONMENT` / `CORS_ORIGINS` / `ALLOWED_HOSTS` |

## Behavior

### Non-production (`ENVIRONMENT` ≠ `production`)

- CORS remains permissive: `allow_origins=["*"]`, all methods/headers (local/dev UX).
- Always-on headers applied; **no** HSTS / CSP (avoids surprising local HTTP and keeps scanner/admin freer).
- TrustedHost **not** installed.

### Production (`ENVIRONMENT=production`)

- `CORS_ORIGINS` is required for useful browser clients: comma-separated absolute origins  
  e.g. `https://admin.example.com,https://scanner.example.com`
- Empty / missing CORS list → no allowed origins (fail closed for browser CORS).
- Methods: standard HTTP verbs + OPTIONS; credentials allowed when origins are explicit.
- HSTS + tight API CSP set via `SecurityHeadersMiddleware`.
- If `ALLOWED_HOSTS` is set (e.g. `api.example.com`), Starlette `TrustedHostMiddleware` is installed; if empty, **skipped** (operator must set for real deployments that need Host validation).

## Env

```bash
ENVIRONMENT=production
CORS_ORIGINS=https://admin.example.com,https://scanner.example.com
ALLOWED_HOSTS=api.example.com
```

## Explicit non-goals / still open

- Not LOCKED / not production-ready / not full ASVS evidence
- No CSRF tokens / SameSite cookie policy pass (session cookies exist elsewhere; not hardened here)
- No multi-worker / Redis-backed rate limit
- No WAF, no full browser-app CSP for Admin Web / Scanner PWA (those frontends own their own CSP)
- No pretence that empty `ALLOWED_HOSTS` is a secure production default — document and set hosts for real prod

## Verify

```bash
cd backend
uv run pytest tests/core/test_config_cors.py tests/core/test_security_headers.py tests/test_health.py -q
```
