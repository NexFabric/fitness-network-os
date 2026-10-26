"""Tests for production fail-closed validation of QR KMS settings."""

import pytest

from app.core.config import Settings, database_ssl_connect_arg

_BASE_PROD = {
    "ENVIRONMENT": "production",
    "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db?sslmode=require",
    "MIGRATOR_DATABASE_URL": None,
    "REDIS_URL": "rediss://localhost:6379/0",
    "CORS_ORIGINS": "https://admin.example.com",
    "ALLOWED_HOSTS": "api.example.com",
    "NOTIFICATION_EMAIL_PROVIDER": "disabled",
    "REPORT_STORAGE_PROVIDER": "s3",
    "S3_BUCKET_NAME": "prod-reports",
    "S3_SSE_ALGORITHM": "aws:kms",
    "S3_KMS_KEY_ID": "arn:aws:kms:eu-central-1:123456789012:key/s3-test",
    "METRICS_BEARER_TOKEN": "x" * 32,
    "ENCRYPTION_KEY": "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=",
}


def test_database_ssl_connect_arg_modes():
    assert database_ssl_connect_arg("postgresql+asyncpg://u:p@h/db") is None
    assert (
        database_ssl_connect_arg("postgresql+asyncpg://u:p@h/db?sslmode=require")
        is True
    )
    ctx = database_ssl_connect_arg("postgresql+asyncpg://u:p@h/db?sslmode=verify-full")
    assert ctx is not None
    assert ctx is not True


def test_production_rejects_s3_sse_aes256():
    s = Settings(
        **{
            **_BASE_PROD,
            "QR_KMS_MODE": "aws_kms",
            "AWS_KMS_KEY_ID": "key-123",
            "S3_SSE_ALGORITHM": "AES256",
        }
    )
    with pytest.raises(
        RuntimeError, match="S3_SSE_ALGORITHM must be aws:kms in production"
    ):
        s.validate_production()


def test_production_rejects_missing_s3_kms_key_id():
    s = Settings(
        **{
            **_BASE_PROD,
            "QR_KMS_MODE": "aws_kms",
            "AWS_KMS_KEY_ID": "key-123",
            "S3_SSE_ALGORITHM": "aws:kms",
            "S3_KMS_KEY_ID": "",
        }
    )
    with pytest.raises(
        RuntimeError, match="S3_KMS_KEY_ID is required when ENVIRONMENT=production"
    ):
        s.validate_production()


def test_production_rejects_smtp_starttls_disabled():
    s = Settings(
        **{
            **_BASE_PROD,
            "QR_KMS_MODE": "aws_kms",
            "AWS_KMS_KEY_ID": "key-123",
            "NOTIFICATION_EMAIL_PROVIDER": "smtp",
            "SMTP_HOST": "smtp.example.com",
            "SMTP_FROM": "noreply@example.com",
            "SMTP_STARTTLS": "0",
        }
    )
    with pytest.raises(
        RuntimeError, match="SMTP_STARTTLS cannot be disabled in production"
    ):
        s.validate_production()


def test_production_rejects_qr_kms_mode_local():
    s = Settings(**{**_BASE_PROD, "QR_KMS_MODE": "local", "AWS_KMS_KEY_ID": "key-123"})
    with pytest.raises(RuntimeError, match="QR_KMS_MODE must be aws_kms in production"):
        s.validate_production()


def test_production_rejects_missing_aws_kms_key_id():
    s = Settings(**{**_BASE_PROD, "QR_KMS_MODE": "aws_kms", "AWS_KMS_KEY_ID": ""})
    with pytest.raises(
        RuntimeError, match="AWS_KMS_KEY_ID is required when ENVIRONMENT=production"
    ):
        s.validate_production()


def test_production_accepts_valid_aws_kms_config():
    s = Settings(
        **{
            **_BASE_PROD,
            "QR_KMS_MODE": "aws_kms",
            "AWS_KMS_KEY_ID": "arn:aws:kms:eu-central-1:123456789012:key/test",
        }
    )
    s.validate_production()  # Does not raise


def test_production_rejects_plaintext_database_without_private_network():
    s = Settings(
        **{
            **_BASE_PROD,
            "QR_KMS_MODE": "aws_kms",
            "AWS_KMS_KEY_ID": "alias/gym-qr",
            "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
        }
    )
    with pytest.raises(RuntimeError, match="sslmode=require"):
        s.validate_production()


def test_production_rejects_plaintext_redis_without_private_network():
    s = Settings(
        **{
            **_BASE_PROD,
            "QR_KMS_MODE": "aws_kms",
            "AWS_KMS_KEY_ID": "alias/gym-qr",
            "REDIS_URL": "redis://localhost:6379/0",
        }
    )
    with pytest.raises(RuntimeError, match="rediss://"):
        s.validate_production()


def test_production_accepts_plaintext_transport_on_private_network():
    s = Settings(
        **{
            **_BASE_PROD,
            "QR_KMS_MODE": "aws_kms",
            "AWS_KMS_KEY_ID": "alias/gym-qr",
            "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
            "REDIS_URL": "redis://localhost:6379/0",
            "PRODUCTION_PRIVATE_NETWORK": "1",
        }
    )
    s.validate_production()


def test_production_rejects_missing_encryption_key():
    s = Settings(
        **{
            **_BASE_PROD,
            "QR_KMS_MODE": "aws_kms",
            "AWS_KMS_KEY_ID": "alias/gym-qr",
            "ENCRYPTION_KEY": "",
        }
    )
    with pytest.raises(RuntimeError, match="ENCRYPTION_KEY"):
        s.validate_production()


def test_production_web_rejects_migrator_dsn():
    s = Settings(
        **{
            **_BASE_PROD,
            "QR_KMS_MODE": "aws_kms",
            "AWS_KMS_KEY_ID": "alias/gym-qr",
            "COMPONENT_NAME": "web",
            "MIGRATOR_DATABASE_URL": (
                "postgresql+asyncpg://u:p@localhost:5432/db?sslmode=require"
            ),
        }
    )
    with pytest.raises(RuntimeError, match="MIGRATOR_DATABASE_URL must not be set"):
        s.validate_production()


def test_production_worker_rejects_migrator_dsn():
    s = Settings(
        **{
            **_BASE_PROD,
            "QR_KMS_MODE": "aws_kms",
            "AWS_KMS_KEY_ID": "alias/gym-qr",
            "COMPONENT_NAME": "worker",
            "NOTIFICATION_EMAIL_PROVIDER": "disabled",
            "MIGRATOR_DATABASE_URL": (
                "postgresql+asyncpg://u:p@localhost:5432/db?sslmode=require"
            ),
        }
    )
    with pytest.raises(RuntimeError, match="MIGRATOR_DATABASE_URL must not be set"):
        s.validate_production()


def test_production_migrate_rejects_plaintext_migrator_dsn():
    s = Settings(
        **{
            **_BASE_PROD,
            "QR_KMS_MODE": "aws_kms",
            "AWS_KMS_KEY_ID": "alias/gym-qr",
            "COMPONENT_NAME": "migrate",
            "NOTIFICATION_EMAIL_PROVIDER": "disabled",
            "MIGRATOR_DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
        }
    )
    with pytest.raises(
        RuntimeError, match="MIGRATOR_DATABASE_URL must include sslmode"
    ):
        s.validate_production()


def test_production_migrate_accepts_tls_migrator_dsn():
    s = Settings(
        **{
            **_BASE_PROD,
            "QR_KMS_MODE": "aws_kms",
            "AWS_KMS_KEY_ID": "alias/gym-qr",
            "COMPONENT_NAME": "migrate",
            "NOTIFICATION_EMAIL_PROVIDER": "disabled",
            "MIGRATOR_DATABASE_URL": (
                "postgresql+asyncpg://u:p@localhost:5432/db?sslmode=verify-full"
            ),
        }
    )
    s.validate_production()
