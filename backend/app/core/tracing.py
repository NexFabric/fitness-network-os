"""Optional OpenTelemetry hook. Default off.

Set OTEL_EXPORTER_OTLP_ENDPOINT to enable. The SDK is not a required
runtime dependency — missing extras log a warning and continue.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger("app.tracing")


def setup_tracing(app: object) -> None:
    endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    if not endpoint:
        return
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError:
        logger.warning(
            "OTEL_EXPORTER_OTLP_ENDPOINT is set but OpenTelemetry is not installed"
        )
        return

    resource = Resource.create({"service.name": "fitness-network-os"})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)  # type: ignore[arg-type]
    except ImportError:
        logger.warning("opentelemetry-instrumentation-fastapi is not installed")
    logger.info("OpenTelemetry export enabled")
