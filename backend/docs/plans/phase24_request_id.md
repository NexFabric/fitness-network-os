# Phase 24 — Request ID correlation

**Status:** 🟠 **IMPLEMENTED on branch** (light MVP) — **not LOCKED**  
**Branch:** `feat/phase16-notifications-reports`  
**Do not claim:** production-ready

> Full observability notes: [`phase24_observability.md`](./phase24_observability.md)

---

## Goal

Propagate a correlation id on every HTTP response via `X-Request-ID` so logs, support, and clients can stitch a single request path.

## Landed

| Item | Detail |
|------|--------|
| Middleware | `RequestLoggingMiddleware` in `app/api/middleware/request_logging.py` |
| Wiring | Registered in `app/main.py` (outermost custom middleware) |
| Incoming | Read `X-Request-ID`; if missing/blank → generate UUID4 |
| Outgoing | Always set response header `X-Request-ID` to the resolved id |
| Bonus | `X-Correlation-ID` (client or mirror of request_id) + safe access log line |
| State | `request.state.request_id` / `request.state.correlation_id` |
| Tests | `tests/core/test_request_id.py`, `tests/test_request_logging.py` |

## Behavior

1. Client sends `X-Request-ID: <opaque>` → same value echoed on response.  
2. Client omits header → server generates UUID and returns it.  
3. Applies to all routes including `/health` (body unchanged; headers only).

## Explicit non-goals (this light MVP)

- No OpenTelemetry / distributed tracing export  
- No secrets/PII/query/body in access logs  
- No persistence of request_id on outbox/audit rows

## Verify

```bash
cd backend
uv run pytest tests/test_health.py tests/core/test_request_id.py tests/test_request_logging.py -q
curl -i http://localhost:8000/health
curl -i -H 'X-Request-ID: client-trace-1' http://localhost:8000/health
```
