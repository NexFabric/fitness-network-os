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
    # Empty → TrustedHostMiddleware is not installed (document and set for real prod).
    # e.g. "api.example.com,localhost"
    ALLOWED_HOSTS: str = ""

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


settings = Settings()  # type: ignore[call-arg]
