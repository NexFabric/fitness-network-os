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
    s = _settings(CORS_ORIGINS="", ENVIRONMENT="local")
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


def test_production_fail_closed_missing_cors_and_hosts():
    s = _settings(ENVIRONMENT="production", CORS_ORIGINS="", ALLOWED_HOSTS="")
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        s.validate_production()


def test_production_ok_with_cors_and_hosts():
    s = _settings(
        ENVIRONMENT="production",
        CORS_ORIGINS="https://admin.example.com",
        ALLOWED_HOSTS="api.example.com",
        NOTIFICATION_EMAIL_PROVIDER="disabled",
        REPORT_STORAGE_PROVIDER="s3",
        S3_BUCKET_NAME="private-reports",
        METRICS_BEARER_TOKEN="m" * 32,
        QR_KMS_MODE="aws_kms",
        AWS_KMS_KEY_ID="alias/gym-qr-signing",
    )
    s.validate_production()  # does not raise


def test_production_rejects_mock_notifications_and_local_reports():
    s = _settings(
        ENVIRONMENT="production",
        CORS_ORIGINS="https://admin.example.com",
        ALLOWED_HOSTS="api.example.com",
    )
    with pytest.raises(RuntimeError) as exc_info:
        s.validate_production()
    message = str(exc_info.value)
    assert "NOTIFICATION_EMAIL_PROVIDER" in message
    assert "REPORT_STORAGE_PROVIDER" in message
    assert "S3_BUCKET_NAME" in message
