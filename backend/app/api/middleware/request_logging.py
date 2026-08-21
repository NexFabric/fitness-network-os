"""Structured request logging + request/correlation ID propagation.

Phase 24 observability stub (MASTER_SPEC §159–162):
- Accept or mint ``X-Request-ID``; echo on the response.
- ``X-Correlation-ID`` prefers client value, else mirrors request_id.
- Log method, path (no query), status, duration, ids only.
- Never log Authorization, cookies, bodies, query strings, PAN/CVV, QR tokens, PII.
"""

from __future__ import annotations

import logging
import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger("app.request")

REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"


def _safe_id(value: str | None) -> str | None:
    """Return a trimmed non-empty id, or None. Caps length to avoid log abuse."""
    if value is None:
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    # Bound header size (UUIDs / short opaque tokens only)
    if len(cleaned) > 128:
        cleaned = cleaned[:128]
    return cleaned


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """ASGI middleware: correlation ids + structured access log (no secrets/PII)."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = _safe_id(request.headers.get(REQUEST_ID_HEADER)) or str(
            uuid.uuid4()
        )
        correlation_id = (
            _safe_id(request.headers.get(CORRELATION_ID_HEADER)) or request_id
        )

        # Available to handlers via request.state if needed later
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id

        start = time.perf_counter()
        status_code = 500
        response: Response | None = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            if response is not None:
                response.headers[REQUEST_ID_HEADER] = request_id
                response.headers[CORRELATION_ID_HEADER] = correlation_id

            tenant_id = None
            try:
                from app.api.deps import current_tenant_id_var

                tenant_id = current_tenant_id_var.get(None)
            except (ImportError, LookupError):
                tenant_id = None

            # Structured single-line log. Path only — never query/body/headers.
            logger.info(
                "method=%s path=%s status=%s duration_ms=%.2f request_id=%s correlation_id=%s tenant_id=%s",
                request.method,
                request.url.path,
                status_code,
                duration_ms,
                request_id,
                correlation_id,
                tenant_id,
            )
