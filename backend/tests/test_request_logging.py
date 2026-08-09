"""Phase 24 observability stub — X-Request-ID / X-Correlation-ID behavior."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_request_id_minted_when_absent():
    response = client.get("/health")
    assert response.status_code == 200
    request_id = response.headers.get("X-Request-ID")
    correlation_id = response.headers.get("X-Correlation-ID")
    assert request_id
    assert correlation_id
    # When client sends neither header, correlation mirrors request_id
    assert correlation_id == request_id


def test_request_id_echoed_from_client():
    response = client.get(
        "/health",
        headers={"X-Request-ID": "client-req-123"},
    )
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "client-req-123"
    assert response.headers.get("X-Correlation-ID") == "client-req-123"


def test_correlation_id_independent_when_provided():
    response = client.get(
        "/health",
        headers={
            "X-Request-ID": "req-aaa",
            "X-Correlation-ID": "corr-bbb",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "req-aaa"
    assert response.headers.get("X-Correlation-ID") == "corr-bbb"
