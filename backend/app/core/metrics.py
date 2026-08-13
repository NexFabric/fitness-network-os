"""Low-cardinality Prometheus instrumentation for API and outbox health."""

from __future__ import annotations

from time import monotonic

from fastapi import Request
from prometheus_client import Counter, Gauge, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

HTTP_REQUESTS = Counter(
    "fitness_network_os_http_requests_total",
    "HTTP responses by method, route template and status.",
    ("method", "route", "status"),
)
HTTP_DURATION = Histogram(
    "fitness_network_os_http_request_duration_seconds",
    "HTTP request latency by method and route template.",
    ("method", "route"),
)
DEPENDENCY_UP = Gauge(
    "fitness_network_os_dependency_up",
    "Whether a required runtime dependency is reachable.",
    ("dependency",),
)
OUTBOX_DISPATCH = Counter(
    "fitness_network_os_outbox_dispatch_total",
    "Outbox dispatch outcomes.",
    ("outcome",),
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        started = monotonic()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            route = request.scope.get("route")
            route_path = getattr(route, "path", "unmatched")
            if route_path != "/metrics":
                labels = (request.method, route_path)
                HTTP_REQUESTS.labels(*labels, str(status_code)).inc()
                HTTP_DURATION.labels(*labels).observe(monotonic() - started)
