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
    # Production requires smtp or disabled (or ALLOW_MOCK_EMAIL=true).
    NOTIFICATION_EMAIL_PROVIDER: str = "console"

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
        # Cookie Secure is enforced via is_production in auth/csrf setters.
        if errors:
            raise RuntimeError(
                "Production configuration invalid: " + "; ".join(errors)
            )


settings = Settings()  # type: ignore[call-arg]
settings.validate_production()
