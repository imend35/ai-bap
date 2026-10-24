"""I manage application configuration and environment settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, make_url

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """I manage application settings from environment variables."""

    # I manage the PostgreSQL connection settings.
    postgres_db: str = Field(default="ai_bap")
    postgres_user: str = Field(default="ai_bap_user")
    postgres_password: SecretStr | None = None
    postgres_host: str = Field(default="127.0.0.1")
    postgres_port: int = Field(default=5433)
    database_url_override: SecretStr | None = Field(
        default=None,
        validation_alias="DATABASE_URL",
    )

    # I configure JWT authentication without exposing the signing secret.
    jwt_secret_key: SecretStr = Field(min_length=32)
    jwt_algorithm: str = Field(default="HS256", pattern="^HS256$")
    jwt_access_token_expire_minutes: int = Field(default=30, ge=1)

    # I disable anonymous account creation unless an operator opts in.
    public_registration_enabled: bool = Field(default=False)

    # I read AI service settings from environment variables.
    # I allow the backend to run without an AI API key.
    openai_api_key: SecretStr | None = None
    openai_model: str = Field(default="gpt-4.1-mini")

        # I restrict browser access to explicitly allowed frontend origins.
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> URL:
        """I build the PostgreSQL connection URL safely."""
        if self.database_url_override is not None:
            database_url = make_url(self.database_url_override.get_secret_value())
            if database_url.get_backend_name() != "postgresql":
                raise ValueError("DATABASE_URL must target PostgreSQL.")
            return database_url.set(drivername="postgresql+psycopg")

        if self.postgres_password is None:
            raise RuntimeError("POSTGRES_PASSWORD is required when DATABASE_URL is unset.")

        return URL.create(
            drivername="postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password.get_secret_value(),
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )


@lru_cache
def get_settings() -> Settings:
    """I return cached application settings."""
    return Settings()
