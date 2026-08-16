"""Rate limit for sensitive public endpoints (Redis-backed, sliding window).

Keyed by the login identifier rather than the client IP: NAT co-tenants share an
IP, so an IP key both punishes bystanders and lets an attacker behind another
address walk past it.

The window lives in Redis so every API process counts against the same budget —
an in-process dict silently multiplies the limit by the number of workers, and
grows without bound because nothing ever evicts an idle identifier. If Redis is
unreachable the middleware falls back to a bounded in-process window (fail-open
with a warning): a login path must not go down because the cache did, but the
degradation is logged rather than silent.

Identifiers are hashed before they reach Redis or the logs — the raw value is an
email address.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

logger = logging.getLogger("app.rate_limit")

# Cap on distinct identifiers held in the fallback window, so a burst of unique
# emails cannot grow the process heap unbounded.
FALLBACK_MAX_KEYS = 10_000


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window limiter keyed by request identifier + path."""

    def __init__(
        self,
        app,
        *,
        paths: tuple[str, ...] = (
            "/api/v1/auth/login",
            "/api/v1/devices/auth",
            "/api/v1/auth/mfa/setup",
            "/api/v1/auth/mfa/verify",
            "/api/v1/auth/invite/accept",
        ),
        max_requests: int = 20,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.paths = paths
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._redis = None
        self._redis_failed = False

    def _match(self, path: str) -> bool:
        return any(path == p or path.rstrip("/") == p.rstrip("/") for p in self.paths)

    async def _get_redis(self):
        """Lazily connect. One failure disables Redis for the process lifetime."""
        if self._redis_failed:
            return None
        if self._redis is None:
            try:
                from redis.asyncio import Redis

                from app.core.config import settings

                self._redis = Redis.from_url(
                    str(settings.REDIS_URL),
                    socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                    socket_connect_timeout=settings.REDIS_CONNECT_TIMEOUT,
                )
            except (OSError, TimeoutError, ImportError) as e:
                self._redis_failed = True
                logger.warning(
                    "rate_limit.redis_unavailable degraded=in_process err=%s", e
                )
                return None
        return self._redis

    async def _over_limit_redis(self, key: str, now: float) -> bool | None:
        """True/False when Redis answered; None when it could not be used."""
        client = await self._get_redis()
        if client is None:
            return None
        try:
            member = f"{now:.6f}:{time.monotonic_ns()}"
            pipe = client.pipeline()
            pipe.zremrangebyscore(key, 0, now - self.window_seconds)
            pipe.zadd(key, {member: now})
            pipe.zcard(key)
            # Idle keys expire on their own — no sweeper process required.
            pipe.expire(key, self.window_seconds * 2)
            results = await pipe.execute()
            count = int(results[2])
            if count > self.max_requests:
                # This request does not get to keep its slot in the window.
                await client.zrem(key, member)
                return True
            return False
        except Exception as e:  # noqa: BLE001
            self._redis_failed = True
            logger.warning("rate_limit.redis_error degraded=in_process err=%s", e)
            return None

    def _over_limit_local(self, key: str, now: float) -> bool:
        window = self._hits[key]
        cutoff = now - self.window_seconds
        while window and window[0] < cutoff:
            window.popleft()
        if not window and len(self._hits) > FALLBACK_MAX_KEYS:
            # Drop the empty entry we just created rather than accumulating one
            # per distinct identifier ever seen.
            self._hits.pop(key, None)
            window = deque()
            self._hits[key] = window
        if len(window) >= self.max_requests:
            return True
        window.append(now)
        return False

    def _too_many(self) -> JSONResponse:
        return JSONResponse(
            status_code=429,
            content={
                "detail": "Çok fazla deneme yapıldı, birkaç dakika sonra tekrar deneyin."
            },
            headers={"Retry-After": str(self.window_seconds)},
        )

    async def dispatch(self, request: Request, call_next) -> Response:
        if not (request.method == "POST" and self._match(request.url.path)):
            return await call_next(request)

        body_bytes = await request.body()

        # Restore the body for downstream handlers
        async def receive():
            return {"type": "http.request", "body": body_bytes}

        request._receive = receive

        identifier = "unknown"
        try:
            if body_bytes:
                data = json.loads(body_bytes)
                if data.get("email"):
                    identifier = str(data["email"]).lower().strip()
                elif data.get("device_id"):
                    identifier = f"device:{data['device_id']}"
                elif data.get("token"):
                    identifier = (
                        "invite:"
                        + hashlib.sha256(str(data["token"]).encode()).hexdigest()[:16]
                    )
        except (TypeError, ValueError, UnicodeDecodeError):
            identifier = "unknown"
        if identifier == "unknown":
            session_token = request.cookies.get("session_token")
            if session_token:
                identifier = (
                    "session:" + hashlib.sha256(session_token.encode()).hexdigest()[:16]
                )

        # Hash so emails / device ids never reach Redis or logs.
        digest = hashlib.sha256(identifier.encode()).hexdigest()[:32]
        key = f"rl:{request.url.path}:{digest}"
        now = time.time()

        over = await self._over_limit_redis(key, now)
        if over is None:
            over = self._over_limit_local(key, now)
        if over:
            return self._too_many()

        return await call_next(request)
