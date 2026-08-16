import hmac
import logging
from datetime import UTC, datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.responses import Response

from app.api.middleware.csrf import CSRFMiddleware
from app.api.middleware.rate_limit import SimpleRateLimitMiddleware
from app.api.middleware.request_logging import RequestLoggingMiddleware
from app.api.v1.api import api_router
from app.core.config import settings
from app.core.metrics import DEPENDENCY_UP, MetricsMiddleware

# Tight default for a JSON API (no HTML assets). Not a full browser app CSP.
_API_CSP = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'"
logger = logging.getLogger("app.error")


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
    # Fail closed before wiring routes when production config is incomplete.
    settings.validate_production()
    settings.assert_runtime_environment_allowed()

    app = FastAPI(
        title="Fitness Network OS",
        version="0.1.0",
        description="Core backend for Fitness Network OS",
    )

    # Last registered runs first on the request path (Starlette).
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(MetricsMiddleware)
    # Phase 24: X-Request-ID / X-Correlation-ID + structured access log (no PII/secrets).
    app.add_middleware(RequestLoggingMiddleware)
    # Redis-backed limiter on unauthenticated / weakly authenticated writes.
    app.add_middleware(
        SimpleRateLimitMiddleware,
        max_requests=settings.RATE_LIMIT_LOGIN_MAX_REQUESTS,
        window_seconds=settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS,
    )
    # CSRF Double-Submit protection (Phase 23)
    app.add_middleware(CSRFMiddleware)

    if settings.is_production:
        if settings.allowed_hosts_list:
            app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=settings.allowed_hosts_list,
            )
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins_list,
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
    else:
        # Permissive local / non-prod UX with credentials support for 5173/5174
        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost:5173",
                "http://localhost:5174",
                "http://127.0.0.1:5173",
                "http://127.0.0.1:5174",
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    @app.get("/health", tags=["ops"])
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
            DEPENDENCY_UP.labels("postgresql").set(1)
        except Exception:  # noqa: BLE001
            checks["db"] = "down"
            DEPENDENCY_UP.labels("postgresql").set(0)

        # Check Redis
        try:
            r = Redis.from_url(
                str(settings.REDIS_URL),
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
            )
            await r.ping()
            await r.aclose()
            checks["redis"] = "up"
            DEPENDENCY_UP.labels("redis").set(1)
        except Exception:  # noqa: BLE001
            checks["redis"] = "down"
            DEPENDENCY_UP.labels("redis").set(0)

        status = "ok" if all(v == "up" for v in checks.values()) else "degraded"

        return {
            "status": status,
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": checks,
        }

    @app.get("/live", tags=["ops"])
    async def liveness_probe():
        return Response(content="OK", status_code=200, media_type="text/plain")

    @app.get("/ready", tags=["ops"])
    async def readiness_probe():
        # Quick check for db/redis
        try:
            from redis.asyncio import Redis
            from sqlalchemy import text

            from app.db.session import engine

            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            r = Redis.from_url(
                str(settings.REDIS_URL),
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
            )
            await r.ping()
            await r.aclose()
            return Response(content="OK", status_code=200, media_type="text/plain")
        except Exception:  # noqa: BLE001
            return Response(
                content="Service Unavailable", status_code=503, media_type="text/plain"
            )

    @app.get("/metrics", tags=["ops"])
    async def metrics_probe(request: Request):
        from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

        if settings.is_production:
            authorization = request.headers.get("authorization", "")
            supplied = authorization.removeprefix("Bearer ")
            if not hmac.compare_digest(supplied, settings.METRICS_BEARER_TOKEN):
                return Response(content="Unauthorized", status_code=401)
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        from app.api.deps import current_tenant_id_var

        logger.exception(
            "request.unhandled request_id=%s tenant_id=%s method=%s path=%s",
            getattr(request.state, "request_id", None),
            current_tenant_id_var.get(),
            request.method,
            request.url.path,
            exc_info=exc,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
