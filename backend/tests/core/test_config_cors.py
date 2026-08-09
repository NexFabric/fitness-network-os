"""Phase 23 — CORS / environment settings parsing (no DB)."""

import pytest

from app.core.config import Settings

_REQUIRED = {
    "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
    "MIGRATOR_DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
    "REDIS_URL": "redis://localhost:6379/0",
}


def _settings(**overrides: str) -> Settings:
    data = {**_REQUIRED, **overrides}
    return Settings(**data)  # type: ignore[arg-type]


def test_cors_origins_empty_default():
    s = _settings()
    assert s.cors_origins_list == []
    assert s.ENVIRONMENT == "local"
    assert s.is_production is False


def test_cors_origins_comma_list_strips_whitespace():
    s = _settings(
        CORS_ORIGINS=" https://admin.example.com ,https://scanner.example.com, ",
    )
    assert s.cors_origins_list == [
        "https://admin.example.com",
        "https://scanner.example.com",
    ]


def test_environment_production_flag():
    s = _settings(ENVIRONMENT="production")
    assert s.is_production is True
    assert s.ENVIRONMENT == "production"


def test_environment_normalized_case():
    s = _settings(ENVIRONMENT="Production")
    assert s.ENVIRONMENT == "production"
    assert s.is_production is True


@pytest.mark.parametrize(
    "env,expected",
    [
        ("local", False),
        ("development", False),
        ("staging", False),
        ("production", True),
    ],
)
def test_is_production_matrix(env: str, expected: bool):
    s = _settings(ENVIRONMENT=env)
    assert s.is_production is expected
