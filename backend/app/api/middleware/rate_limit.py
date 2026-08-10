"""Lightweight in-memory rate limit for sensitive public endpoints.

Not multi-worker safe — MVP guardrail only (Phase 23 baseline).
"""

from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding-window limiter keyed by client IP + path."""

    def __init__(
        self,
        app,
        *,
        paths: tuple[str, ...] = ("/api/v1/auth/login",),
        max_requests: int = 20,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.paths = paths
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def _match(self, path: str) -> bool:
        return any(path == p or path.rstrip("/") == p.rstrip("/") for p in self.paths)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.method == "POST" and self._match(request.url.path):
            client = request.client.host if request.client else "unknown"
            key = f"{client}:{request.url.path}"
            now = time.monotonic()
            window = self._hits[key]
            cutoff = now - self.window_seconds
            while window and window[0] < cutoff:
                window.popleft()
            if len(window) >= self.max_requests:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Try again later."},
                    headers={"Retry-After": str(self.window_seconds)},
                )
            window.append(now)
        return await call_next(request)
