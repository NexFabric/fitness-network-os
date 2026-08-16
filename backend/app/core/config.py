import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

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
    SMTP_STARTTLS: str = "1"

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
    ENCRYPTION_KEY: str = ""

    # Login rate limit budget (per identifier, sliding window). Production keeps
    # the tight default; the dev stack raises it so a parallel e2e run against a
    # handful of shared accounts is not throttled into failure.
    RATE_LIMIT_LOGIN_MAX_REQUESTS: int = 20
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 60

    COMPONENT_NAME: str = "web"
    DATABASE_URL: PostgresDsn
    MIGRATOR_DATABASE_URL: PostgresDsn | None = None
    REDIS_URL: RedisDsn
    # Explicit operator attestation that Postgres/Redis sit on a private
    # network (VPC / RFC1918) and therefore may use redis:// without
    # rediss:// or a DSN without sslmode. Public endpoints still refuse
    # plaintext. Documented in docs/ops/PRODUCTION_DEPLOY.md.
    PRODUCTION_PRIVATE_NETWORK: bool = False

    # Database connection pool
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_STATEMENT_TIMEOUT_MS: int = 30000  # 30s server-side query timeout
    DB_COMMAND_TIMEOUT: int = 30  # 30s asyncpg command timeout

    # Redis timeouts
    REDIS_SOCKET_TIMEOUT: float = 5.0
    REDIS_CONNECT_TIMEOUT: float = 5.0

    # S3/boto3 timeouts
    S3_CONNECT_TIMEOUT: int = 10
    S3_READ_TIMEOUT: int = 30

    # QR KMS settings
    QR_KMS_MODE: str = "local"
    AWS_KMS_KEY_ID: str | None = None

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
        is_web = self.COMPONENT_NAME == "web"

        if is_web:
            if not self.cors_origins_list:
                errors.append(
                    "CORS_ORIGINS must be a non-empty comma-separated list in production"
                )
            else:
                for origin in self.cors_origins_list:
                    if not origin.lower().startswith("https://"):
                        errors.append(
                            "CORS origin must start with https:// in production: "
                            + origin
                        )
            if not self.allowed_hosts_list:
                errors.append(
                    "ALLOWED_HOSTS must be a non-empty comma-separated list in production"
                )
            if len(self.METRICS_BEARER_TOKEN) < 32:
                errors.append(
                    "METRICS_BEARER_TOKEN must contain at least 32 characters"
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
            if self.SMTP_STARTTLS.strip() == "0":
                errors.append("SMTP_STARTTLS cannot be disabled in production")

        storage_provider = self.REPORT_STORAGE_PROVIDER.strip().lower()
        if storage_provider != "s3":
            errors.append("REPORT_STORAGE_PROVIDER must be s3 in production")
        if not self.S3_BUCKET_NAME.strip():
            errors.append("S3_BUCKET_NAME is required for production report storage")
        if not 60 <= self.REPORT_DOWNLOAD_URL_TTL_SECONDS <= 3600:
            errors.append("REPORT_DOWNLOAD_URL_TTL_SECONDS must be between 60 and 3600")
        if self.S3_SSE_ALGORITHM != "aws:kms":
            errors.append("S3_SSE_ALGORITHM must be aws:kms in production")
        if not self.S3_KMS_KEY_ID or not self.S3_KMS_KEY_ID.strip():
            errors.append("S3_KMS_KEY_ID is required when ENVIRONMENT=production")

        qr_kms_mode = self.QR_KMS_MODE.strip().lower()
        if qr_kms_mode != "aws_kms":
            errors.append("QR_KMS_MODE must be aws_kms in production")
        if not self.AWS_KMS_KEY_ID or not self.AWS_KMS_KEY_ID.strip():
            errors.append("AWS_KMS_KEY_ID is required when ENVIRONMENT=production")

        if not _is_valid_fernet_key(self.ENCRYPTION_KEY):
            errors.append("ENCRYPTION_KEY must be a valid Fernet key")

        component = (self.COMPONENT_NAME or "web").strip().lower()
        if component in {"web", "worker"} and self.MIGRATOR_DATABASE_URL is not None:
            errors.append(
                "MIGRATOR_DATABASE_URL must not be set on long-lived processes; "
                "it belongs only on COMPONENT_NAME=migrate"
            )

        if not self.PRODUCTION_PRIVATE_NETWORK:
            db_sslmode = _dsn_query_param(str(self.DATABASE_URL), "sslmode")
            if db_sslmode not in {"require", "verify-full"}:
                errors.append(
                    "DATABASE_URL must include sslmode=require or sslmode=verify-full "
                    "unless PRODUCTION_PRIVATE_NETWORK=1"
                )
            if not str(self.REDIS_URL).startswith("rediss://"):
                errors.append(
                    "REDIS_URL must use rediss:// unless PRODUCTION_PRIVATE_NETWORK=1"
                )
            if self.MIGRATOR_DATABASE_URL is not None:
                mig_sslmode = _dsn_query_param(
                    str(self.MIGRATOR_DATABASE_URL), "sslmode"
                )
                if mig_sslmode not in {"require", "verify-full"}:
                    errors.append(
                        "MIGRATOR_DATABASE_URL must include sslmode=require or "
                        "sslmode=verify-full unless PRODUCTION_PRIVATE_NETWORK=1"
                    )

        if errors:
            raise RuntimeError("Production configuration invalid: " + "; ".join(errors))

    def assert_runtime_environment_allowed(
        self, *, pytest_loaded: bool | None = None
    ) -> None:
        """Refuse ENVIRONMENT=test outside pytest so CSRF/crypto kill-switches cannot ship."""
        if self.ENVIRONMENT != "test":
            return
        if pytest_loaded is None:
            import sys

            pytest_loaded = "pytest" in sys.modules
        if not pytest_loaded:
            raise RuntimeError(
                "ENVIRONMENT=test is only valid under pytest. "
                "Use local, development, staging, or production."
            )


def _dsn_query_param(url: str, name: str) -> str:
    values = parse_qs(urlparse(url).query).get(name, [])
    return values[-1].strip().lower() if values else ""


def database_ssl_connect_arg(database_url: str) -> object | None:
    """asyncpg ssl= value for a production DSN, or None when TLS is not requested."""
    sslmode = _dsn_query_param(database_url, "sslmode")
    if sslmode == "verify-full":
        import ssl

        return ssl.create_default_context()
    if sslmode == "require":
        return True
    return None


def _is_valid_fernet_key(key: str) -> bool:
    if not key or not str(key).strip():
        return False
    try:
        from cryptography.fernet import Fernet

        Fernet(str(key).strip().encode())
    except (ValueError, TypeError):
        return False
    return True


settings = Settings()  # type: ignore[call-arg]
settings.validate_production()
