# Phase 24 — Observability (X-Request-ID + structured access log)

**Status:** 🟠 **IMPLEMENTED on branch** (light MVP) — **not LOCKED** · **not production-ready**  
**Branch:** `feat/phase16-notifications-reports`  
**Plan path:** `backend/docs/plans/phase24_observability.md`

---

## Goal

Minimal, safe request observability:

- Every HTTP response carries `X-Request-ID` (echo client or mint UUID4)
- `X-Correlation-ID` prefers client value, else mirrors request id
- One structured access log line per request (no secrets/PII)

---

## Landed

| Item | Detail |
|------|--------|
| Middleware | `backend/app/api/middleware/request_logging.py` → `RequestLoggingMiddleware` |
| Wiring | Registered in `backend/app/main.py` (outermost of custom middleware) |
| Request id | Accept `X-Request-ID` if non-blank (max 128 chars); else UUID4 |
| Correlation id | Accept `X-Correlation-ID` if present; else = request_id |
| Response | Both headers set on response |
| Access log | `method path status duration_ms request_id correlation_id` via logger `app.request` |
| State | `request.state.request_id` / `request.state.correlation_id` |
| Tests | `tests/test_request_logging.py`, `tests/core/test_request_id.py` |

### Hard rules

**Never log:** Authorization, cookies, bodies, query strings, PAN/CVV, QR tokens, PII.

### Explicit non-goals

- OpenTelemetry / distributed tracing
- JSON/structlog dependency
- Business metrics (QR latency, outbox backlog, …)
- Auto-inject tenant_id/user_id into every log line
- Correlation on outbox worker path

---

## Verify

```bash
cd backend
uv run pytest tests/test_request_logging.py tests/core/test_request_id.py tests/test_health.py -q
curl -i http://localhost:8000/health
curl -i -H 'X-Request-ID: client-trace-1' http://localhost:8000/health
```

---

## Status honesty

**IMPLEMENTED on branch** only. Not LOCKED until merge + green main CI. Does **not** complete production observability. Phase 26 exit gate **not passed**.
