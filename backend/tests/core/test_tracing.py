from app.core.tracing import setup_tracing


def test_setup_tracing_noop_without_endpoint(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    setup_tracing(object())


def test_setup_tracing_warns_when_sdk_missing(monkeypatch, caplog):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")
    setup_tracing(object())
