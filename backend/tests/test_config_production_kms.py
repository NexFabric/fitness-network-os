"""Tests for production fail-closed validation of QR KMS settings."""

import pytest

from app.core.config import Settings

_BASE_PROD = {
    "ENVIRONMENT": "production",
    "DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
    "MIGRATOR_DATABASE_URL": "postgresql+asyncpg://u:p@localhost:5432/db",
    "REDIS_URL": "redis://localhost:6379/0",
    "CORS_ORIGINS": "https://admin.example.com",
    "ALLOWED_HOSTS": "api.example.com",
    "NOTIFICATION_EMAIL_PROVIDER": "disabled",
    "REPORT_STORAGE_PROVIDER": "s3",
    "S3_BUCKET_NAME": "prod-reports",
    "METRICS_BEARER_TOKEN": "x" * 32,
    "ENCRYPTION_KEY": "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=",
}


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
