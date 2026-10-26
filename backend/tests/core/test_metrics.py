from fastapi.testclient import TestClient

from app.main import app


def test_metrics_exposes_real_request_counters():
    with TestClient(app) as client:
        assert client.get("/live").status_code == 200
        response = client.get("/metrics")
    assert response.status_code == 200
    assert "fitness_network_os_http_requests_total" in response.text
    assert "fitness_network_os_http_request_duration_seconds" in response.text
