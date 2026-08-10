import secrets

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class CSRFMiddleware(BaseHTTPMiddleware):
    """Simple Double-Submit Cookie CSRF Middleware.
    
    Checks that a valid CSRF token is sent in both a cookie and a custom header
    for all state-changing requests (POST, PUT, PATCH, DELETE).
    """

    SAFE_METHODS: frozenset[str] = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
    EXEMPT_PATHS: frozenset[str] = frozenset({"/api/v1/auth/login", "/api/v1/auth/logout"})
    COOKIE_NAME = "csrf_token"
    HEADER_NAME = "x-csrf-token"

    async def dispatch(self, request: Request, call_next) -> Response:
        from app.core.config import settings

        # Bypass CSRF for tests
        if settings.ENVIRONMENT == "test":
            return await call_next(request)

        csrf_cookie = request.cookies.get(self.COOKIE_NAME)
        
        # Ensure every request gets a CSRF cookie if it doesn't have one
        if not csrf_cookie:
            csrf_cookie = secrets.token_urlsafe(32)

        # For unsafe methods, validate the header against the cookie
        if request.method not in self.SAFE_METHODS and request.url.path not in self.EXEMPT_PATHS:
            csrf_header = request.headers.get(self.HEADER_NAME)
            
            # Simple constant-time comparison is recommended for tokens, 
            # but string equality works for basic double-submit where the secret 
            # is just the random value itself.
            if not csrf_header or csrf_header != csrf_cookie:
                return Response(content="CSRF token validation failed", status_code=403)

        response = await call_next(request)
        
        # Always set/refresh the cookie
        response.set_cookie(
            key=self.COOKIE_NAME,
            value=csrf_cookie,
            httponly=False,  # Must be readable by JavaScript
            samesite="lax",
            path="/",
        )
        
        return response
