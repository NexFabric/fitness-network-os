"""Double-submit CSRF: cookie + X-CSRF-Token header on unsafe methods.

Cross-origin admin (e.g. :5173 → :8000) cannot read the API cookie via
document.cookie. Clients must bootstrap via GET /api/v1/auth/csrf which
returns the token in JSON (same value as cookie on API origin).
"""

from __future__ import annotations

import hmac
import secrets

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class CSRFMiddleware(BaseHTTPMiddleware):
    SAFE_METHODS: frozenset[str] = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
    EXEMPT_PATHS: frozenset[str] = frozenset(
        {
            "/api/v1/auth/login",
            "/api/v1/auth/csrf",
            "/api/v1/auth/invite/accept",
            "/api/v1/devices/auth",
        }
    )
    COOKIE_NAME = "csrf_token"
    HEADER_NAME = "x-csrf-token"

    async def dispatch(self, request: Request, call_next) -> Response:
        from app.core.config import settings

        # Test suite uses Bearer + ASGI; opt-in real CSRF with X-Test-CSRF: enforce
        if (
            settings.ENVIRONMENT == "test"
            and request.headers.get("x-test-csrf") != "enforce"
        ):
            return await call_next(request)

        csrf_cookie = request.cookies.get(self.COOKIE_NAME)
        if not csrf_cookie:
            csrf_cookie = secrets.token_urlsafe(32)
        # Single source of truth for this request (auth/csrf endpoint reads it)
        request.state.csrf_token = csrf_cookie

        # ASVS 4.0.3: an explicit Authorization: Bearer header is not an ambient
        # credential, so it is exempt. The exemption only holds while no session
        # cookie is present: get_session_token_from_cookie prefers the cookie, so
        # a request carrying both would authenticate ambiently but skip the check
        # on the strength of an attacker-supplied header.
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith(("Bearer ", "bearer ")) and not request.cookies.get(
            "session_token"
        ):
            return await call_next(request)

        if (
            request.method not in self.SAFE_METHODS
            and request.url.path not in self.EXEMPT_PATHS
        ):
            csrf_header = request.headers.get(self.HEADER_NAME)
            if not csrf_header or not hmac.compare_digest(
                str(csrf_header), str(csrf_cookie)
            ):
                resp = JSONResponse(
                    status_code=403,
                    content={"detail": "CSRF token validation failed"},
                )
                self._set_csrf_cookie(resp, csrf_cookie, settings)
                return resp

        response = await call_next(request)
        self._set_csrf_cookie(response, csrf_cookie, settings)
        return response

    def _set_csrf_cookie(self, response: Response, value: str, settings) -> None:
        response.set_cookie(
            key=self.COOKIE_NAME,
            value=value,
            httponly=False,
            samesite="lax",
            secure=settings.is_production,
            path="/",
            max_age=7 * 24 * 3600,
        )
