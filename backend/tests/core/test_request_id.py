"""Phase 24 — X-Request-ID middleware (no DB)."""

from uuid import UUID

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_generates_request_id_when_missing():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    rid = response.headers.get("X-Request-ID")
    assert rid
    # uuid4 string form
    UUID(rid)


def test_health_echoes_client_request_id():
    response = client.get("/health", headers={"X-Request-ID": "client-trace-abc"})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "client-trace-abc"


def test_blank_request_id_is_replaced():
    response = client.get("/health", headers={"X-Request-ID": "   "})
    assert response.status_code == 200
    rid = response.headers.get("X-Request-ID")
    assert rid
    assert rid.strip()
    UUID(rid)
