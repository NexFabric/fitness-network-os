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
WORKER_HEARTBEAT = Gauge(
    "fitness_network_os_worker_heartbeat_timestamp_seconds",
    "Timestamp of last completed worker cycle.",
    ("worker",),
)
NOTIFICATION_DISPATCH = Counter(
    "fitness_network_os_notification_dispatch_total",
    "Notification delivery outcomes.",
    ("channel", "outcome"),
)
REPORT_EXECUTION = Counter(
    "fitness_network_os_report_execution_total",
    "Report execution outcomes.",
    ("outcome",),
)
RETENTION_RECORDS = Counter(
    "fitness_network_os_retention_records_total",
    "Retention sweep records removed.",
    ("model",),
)


def start_worker_metrics_server(port: int | None = None) -> bool:
    """Start an in-process HTTP metrics server for worker observability."""
    import logging
    import os

    logger = logging.getLogger(__name__)
    port_env = os.environ.get("METRICS_PORT")
    target_port = port or (int(port_env) if port_env and port_env.isdigit() else None)
    if not target_port:
        return False
    try:
        from prometheus_client import start_http_server

        start_http_server(target_port, addr="0.0.0.0")
        logger.info("Worker metrics server started on port %d", target_port)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Failed to start worker metrics server on port %d: %s", target_port, exc
        )
        return False


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
