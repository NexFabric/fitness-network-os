from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response

from app.api.middleware.rate_limit import SimpleRateLimitMiddleware
from app.api.middleware.request_logging import RequestLoggingMiddleware
from app.api.middleware.csrf import CSRFMiddleware
from app.api.v1.api import api_router
from app.core.config import settings

# Tight default for a JSON API (no HTML assets). Not a full browser app CSP.
_API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Browser security headers (Phase 23).

    Always: nosniff, frame DENY, Referrer-Policy.
    Production only: HSTS + tight CSP for JSON API.
    Not a full ASVS / cookie / CSRF suite.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy",
            "strict-origin-when-cross-origin",
        )
        if settings.is_production:
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains",
            )
            response.headers.setdefault("Content-Security-Policy", _API_CSP)
        return response


def create_app() -> FastAPI:
    app = FastAPI(
        title="Fitness Network OS",
        version="0.1.0",
        description="Core backend for Fitness Network OS",
    )

    if settings.is_production:
        # Fail closed for browser CORS when ENVIRONMENT=production
        origins = settings.cors_origins_list
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
    else:
        # Permissive local / non-prod UX (existing behavior)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # Last registered runs first on the request path (Starlette).
    app.add_middleware(SecurityHeadersMiddleware)
    # Phase 24 stub: X-Request-ID / X-Correlation-ID + structured access log (no PII/secrets).
    app.add_middleware(RequestLoggingMiddleware)
    # Light in-process rate limit on POST /api/v1/auth/login (MVP; not multi-worker).
    app.add_middleware(SimpleRateLimitMiddleware)

    # Production Host allowlist only when ALLOWED_HOSTS is non-empty (skip if unset).
    if settings.is_production and settings.allowed_hosts_list:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.allowed_hosts_list,
        )

    # CSRF Double-Submit protection (Phase 23)
    app.add_middleware(CSRFMiddleware)

    @app.get("/health")
    async def health_check():
        from redis.asyncio import Redis
        from sqlalchemy import text

        from app.db.session import engine
        
        checks = {}
        
        # Check DB
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            checks["db"] = "up"
        except Exception:
            checks["db"] = "down"
            
        # Check Redis
        try:
            r = Redis.from_url(str(settings.REDIS_URL))
            await r.ping()
            await r.aclose()
            checks["redis"] = "up"
        except Exception:
            checks["redis"] = "down"
            
        status = "ok" if all(v == "up" for v in checks.values()) else "degraded"

        return {
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": checks,
        }

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
