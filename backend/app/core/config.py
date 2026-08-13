import tempfile
from pathlib import Path

from pydantic import PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Fitness Network OS"
    VERSION: str = "0.1.0"

    # local | development | staging | production — production tightens CORS / headers
    ENVIRONMENT: str = "local"
    # Comma-separated absolute origins used when ENVIRONMENT=production
    # e.g. "https://admin.example.com,https://scanner.example.com"
    CORS_ORIGINS: str = ""
    # Comma-separated Host values for Starlette TrustedHostMiddleware when production.
    # Production requires non-empty (fail-closed at boot).
    # e.g. "api.example.com,localhost"
    ALLOWED_HOSTS: str = ""

    # EMAIL notification adapter: log | console | smtp | disabled
    # Production requires smtp or disabled.
    NOTIFICATION_EMAIL_PROVIDER: str = "console"
    SMTP_HOST: str = ""
    SMTP_FROM: str = ""

    # Report artifacts are local in development/test and private S3-compatible
    # objects in production. Credentials use the standard AWS environment
    # variables and are deliberately not represented here.
    REPORT_STORAGE_PROVIDER: str = "local"
    REPORT_STORAGE_DIR: str = str(
        Path(tempfile.gettempdir()) / "fitness-network-os-reports"
    )
    REPORT_DOWNLOAD_URL_TTL_SECONDS: int = 900
    S3_BUCKET_NAME: str = ""
    S3_ENDPOINT_URL: str = ""
    S3_REGION_NAME: str = ""
    S3_SSE_ALGORITHM: str = "AES256"
    S3_KMS_KEY_ID: str = ""
    METRICS_BEARER_TOKEN: str = ""

    # Login rate limit budget (per identifier, sliding window). Production keeps
    # the tight default; the dev stack raises it so a parallel e2e run against a
    # handful of shared accounts is not throttled into failure.
    RATE_LIMIT_LOGIN_MAX_REQUESTS: int = 20
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 60

    DATABASE_URL: PostgresDsn
    MIGRATOR_DATABASE_URL: PostgresDsn
    REDIS_URL: RedisDsn

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )

    @field_validator("ENVIRONMENT", mode="before")
    @classmethod
    def _normalize_environment(cls, v: object) -> str:
        if v is None or v == "":
            return "local"
        return str(v).strip().lower()

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS_ORIGINS env (comma-separated) into a clean list."""
        if not self.CORS_ORIGINS or not str(self.CORS_ORIGINS).strip():
            return []
        return [
            part.strip() for part in str(self.CORS_ORIGINS).split(",") if part.strip()
        ]

    @property
    def allowed_hosts_list(self) -> list[str]:
        """Parse ALLOWED_HOSTS env (comma-separated) into a clean list."""
        if not self.ALLOWED_HOSTS or not str(self.ALLOWED_HOSTS).strip():
            return []
        return [
            part.strip() for part in str(self.ALLOWED_HOSTS).split(",") if part.strip()
        ]

    def validate_production(self) -> None:
        """Fail closed when ENVIRONMENT=production and critical security config is missing."""
        if not self.is_production:
            return
        errors: list[str] = []
        if not self.cors_origins_list:
            errors.append(
                "CORS_ORIGINS must be a non-empty comma-separated list in production"
            )
        if not self.allowed_hosts_list:
            errors.append(
                "ALLOWED_HOSTS must be a non-empty comma-separated list in production"
            )
        email_provider = self.NOTIFICATION_EMAIL_PROVIDER.strip().lower()
        if email_provider not in {"smtp", "disabled"}:
            errors.append(
                "NOTIFICATION_EMAIL_PROVIDER must be smtp or disabled in production"
            )
        if email_provider == "smtp":
            if not self.SMTP_HOST.strip():
                errors.append("SMTP_HOST is required when SMTP delivery is enabled")
            if not self.SMTP_FROM.strip():
                errors.append("SMTP_FROM is required when SMTP delivery is enabled")

        storage_provider = self.REPORT_STORAGE_PROVIDER.strip().lower()
        if storage_provider != "s3":
            errors.append("REPORT_STORAGE_PROVIDER must be s3 in production")
        if not self.S3_BUCKET_NAME.strip():
            errors.append("S3_BUCKET_NAME is required for production report storage")
        if not 60 <= self.REPORT_DOWNLOAD_URL_TTL_SECONDS <= 3600:
            errors.append("REPORT_DOWNLOAD_URL_TTL_SECONDS must be between 60 and 3600")
        if self.S3_SSE_ALGORITHM not in {"AES256", "aws:kms"}:
            errors.append("S3_SSE_ALGORITHM must be AES256 or aws:kms")
        if self.S3_SSE_ALGORITHM == "aws:kms" and not self.S3_KMS_KEY_ID.strip():
            errors.append("S3_KMS_KEY_ID is required when S3_SSE_ALGORITHM=aws:kms")
        if len(self.METRICS_BEARER_TOKEN) < 32:
            errors.append("METRICS_BEARER_TOKEN must contain at least 32 characters")
        # Cookie Secure is enforced via is_production in auth/csrf setters.
        if errors:
            raise RuntimeError("Production configuration invalid: " + "; ".join(errors))


settings = Settings()  # type: ignore[call-arg]
settings.validate_production()
