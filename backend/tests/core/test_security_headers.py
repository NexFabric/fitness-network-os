"""Phase 23 — security headers + ALLOWED_HOSTS parsing (no DB)."""

from collections.abc import Iterator
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import Settings
from app.main import _API_CSP, SecurityHeadersMiddleware, create_app


def _patch_settings(**kwargs):
    """spec=Settings so MagicMock allows assert_* methods on the real Settings API."""
    return patch("app.main.settings", spec=Settings, **kwargs)

_REQUIRED = {
    "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
    "MIGRATOR_DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
    "REDIS_URL": "redis://localhost:6379/0",
}


def _settings(**overrides: str) -> Settings:
    data = {**_REQUIRED, **overrides}
    return Settings(**data)  # type: ignore[arg-type]


def _headers_client(*, production: bool) -> Iterator[TestClient]:
    app = FastAPI()

    @app.get("/ping")
    def ping():
        return {"ok": True}

    app.add_middleware(SecurityHeadersMiddleware)
    with patch("app.main.settings") as mock_settings:
        mock_settings.is_production = production
        mock_settings.validate_production.return_value = None
        yield TestClient(app)


@pytest.fixture
def non_prod_client() -> Iterator[TestClient]:
    yield from _headers_client(production=False)


@pytest.fixture
def prod_client() -> Iterator[TestClient]:
    yield from _headers_client(production=True)


def test_allowed_hosts_empty_default():
    s = _settings()
    assert s.allowed_hosts_list == []


def test_allowed_hosts_comma_list_strips_whitespace():
    s = _settings(ALLOWED_HOSTS=" api.example.com , localhost , ")
    assert s.allowed_hosts_list == ["api.example.com", "localhost"]


def test_non_prod_headers_baseline(non_prod_client: TestClient):
    r = non_prod_client.get("/ping")
    assert r.status_code == 200
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "Strict-Transport-Security" not in r.headers
    assert "Content-Security-Policy" not in r.headers


def test_prod_headers_include_hsts_and_csp(prod_client: TestClient):
    r = prod_client.get("/ping")
    assert r.status_code == 200
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert (
        r.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
    )
    assert r.headers["Content-Security-Policy"] == _API_CSP


def test_create_app_trusted_host_only_when_prod_and_hosts_set():
    """TrustedHostMiddleware installed only for production + non-empty ALLOWED_HOSTS."""
    with _patch_settings() as mock_settings:
        mock_settings.is_production = True
        mock_settings.validate_production.return_value = None
        mock_settings.assert_runtime_environment_allowed.return_value = None
        mock_settings.cors_origins_list = []
        mock_settings.allowed_hosts_list = ["api.example.com"]
        mock_settings.RATE_LIMIT_LOGIN_MAX_REQUESTS = 20
        mock_settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS = 60
        app = create_app()
        middleware_types = [m.cls for m in app.user_middleware]
        assert TrustedHostMiddleware in middleware_types


def test_create_app_no_trusted_host_when_hosts_empty():
    with _patch_settings() as mock_settings:
        mock_settings.is_production = True
        mock_settings.validate_production.return_value = None
        mock_settings.assert_runtime_environment_allowed.return_value = None
        mock_settings.cors_origins_list = []
        mock_settings.allowed_hosts_list = []
        mock_settings.RATE_LIMIT_LOGIN_MAX_REQUESTS = 20
        mock_settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS = 60
        app = create_app()
        middleware_types = [m.cls for m in app.user_middleware]
        assert TrustedHostMiddleware not in middleware_types


def test_create_app_no_trusted_host_non_prod():
    with _patch_settings() as mock_settings:
        mock_settings.is_production = False
        mock_settings.validate_production.return_value = None
        mock_settings.assert_runtime_environment_allowed.return_value = None
        mock_settings.cors_origins_list = []
        mock_settings.allowed_hosts_list = ["api.example.com"]
        mock_settings.RATE_LIMIT_LOGIN_MAX_REQUESTS = 20
        mock_settings.RATE_LIMIT_LOGIN_WINDOW_SECONDS = 60
        app = create_app()
        middleware_types = [m.cls for m in app.user_middleware]
        assert TrustedHostMiddleware not in middleware_types
