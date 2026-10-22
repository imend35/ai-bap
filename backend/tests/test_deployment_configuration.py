"""I verify the database configuration used by managed deployment platforms."""

import pytest

from app.config import Settings


def test_database_url_override_uses_the_psycopg_driver(monkeypatch: pytest.MonkeyPatch) -> None:
    """I prefer a managed PostgreSQL URL without requiring local DB variables."""
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://deployment_user:deployment_password@private-db:5432/ai_bap",
    )
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    monkeypatch.setenv("JWT_SECRET_KEY", "deployment-test-jwt-secret-key-000000000000")

    settings = Settings(_env_file=None)

    assert settings.database_url.drivername == "postgresql+psycopg"
    assert settings.database_url.host == "private-db"
    assert settings.database_url.database == "ai_bap"


def test_database_configuration_fails_closed_without_a_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """I reject incomplete database configuration before an engine is created."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    monkeypatch.setenv("JWT_SECRET_KEY", "deployment-test-jwt-secret-key-000000000000")

    settings = Settings(_env_file=None)

    with pytest.raises(RuntimeError, match="POSTGRES_PASSWORD"):
        _ = settings.database_url
