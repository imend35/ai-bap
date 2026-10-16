"""I enforce fail-closed configuration for PostgreSQL integration tests."""

import os
from collections.abc import MutableMapping
from typing import Any


TEST_MODE_VALUE = "true"
TEST_CONFIRMATION_VALUE = "isolated-postgresql-acknowledged"
TEST_DATABASE_SETTINGS = {
    "POSTGRES_HOST": "127.0.0.1",
    "POSTGRES_PORT": "55432",
    "POSTGRES_DB": "ai_bap_test",
    "POSTGRES_USER": "ai_bap_test_user",
}
LEGACY_MIGRATION_TEST_TARGET = "legacy-migration"
LEGACY_MIGRATION_TEST_CONFIRMATION_VALUE = "legacy-migration-postgresql-acknowledged"
LEGACY_MIGRATION_TEST_DATABASE_SETTINGS = {
    "POSTGRES_HOST": "127.0.0.1",
    "POSTGRES_PORT": "55433",
    "POSTGRES_DB": "ai_bap_legacy_test",
    "POSTGRES_USER": "ai_bap_legacy_test_user",
}


class IntegrationDatabaseSafetyError(RuntimeError):
    """I report an unsafe integration-test database configuration."""


def configure_test_database_environment(
    environment: MutableMapping[str, str] | None = None,
) -> None:
    """Validate explicit test settings before application database imports."""
    target_environment = environment if environment is not None else os.environ

    if target_environment.get("AI_BAP_TEST_MODE") != TEST_MODE_VALUE:
        raise IntegrationDatabaseSafetyError(
            "Integration tests require AI_BAP_TEST_MODE=true."
        )

    if (
        target_environment.get("AI_BAP_TEST_DATABASE_CONFIRMATION")
        != TEST_CONFIRMATION_VALUE
    ):
        raise IntegrationDatabaseSafetyError(
            "Integration tests require explicit isolated database confirmation."
        )

    for setting_name, expected_value in TEST_DATABASE_SETTINGS.items():
        actual_value = target_environment.get(setting_name)
        if actual_value != expected_value:
            raise IntegrationDatabaseSafetyError(
                f"{setting_name} must be {expected_value!r} for integration tests."
            )

    test_password = target_environment.get("AI_BAP_TEST_POSTGRES_PASSWORD")
    if not test_password or target_environment.get("POSTGRES_PASSWORD") != test_password:
        raise IntegrationDatabaseSafetyError(
            "Integration tests require POSTGRES_PASSWORD to match the explicit "
            "AI_BAP_TEST_POSTGRES_PASSWORD value."
        )

    # I reapply verified values so they override values loaded from .env later.
    target_environment.update(TEST_DATABASE_SETTINGS)


def configure_legacy_migration_test_database_environment(
    environment: MutableMapping[str, str] | None = None,
) -> None:
    """Validate the separately approved legacy-migration database target."""
    target_environment = environment if environment is not None else os.environ

    if target_environment.get("AI_BAP_TEST_MODE") != TEST_MODE_VALUE:
        raise IntegrationDatabaseSafetyError(
            "Legacy migration validation requires AI_BAP_TEST_MODE=true."
        )

    if (
        target_environment.get("AI_BAP_ALEMBIC_TARGET")
        != LEGACY_MIGRATION_TEST_TARGET
    ):
        raise IntegrationDatabaseSafetyError(
            "Legacy migration validation requires the explicit legacy target selector."
        )

    if (
        target_environment.get("AI_BAP_LEGACY_TEST_DATABASE_CONFIRMATION")
        != LEGACY_MIGRATION_TEST_CONFIRMATION_VALUE
    ):
        raise IntegrationDatabaseSafetyError(
            "Legacy migration validation requires explicit database confirmation."
        )

    for (
        setting_name,
        expected_value,
    ) in LEGACY_MIGRATION_TEST_DATABASE_SETTINGS.items():
        actual_value = target_environment.get(setting_name)
        if actual_value != expected_value:
            raise IntegrationDatabaseSafetyError(
                f"{setting_name} must be {expected_value!r} for legacy migration validation."
            )

    test_password = target_environment.get("AI_BAP_LEGACY_TEST_POSTGRES_PASSWORD")
    if (
        not test_password
        or target_environment.get("POSTGRES_PASSWORD") != test_password
    ):
        raise IntegrationDatabaseSafetyError(
            "Legacy migration validation requires POSTGRES_PASSWORD to match the "
            "explicit AI_BAP_LEGACY_TEST_POSTGRES_PASSWORD value."
        )

    target_environment.update(LEGACY_MIGRATION_TEST_DATABASE_SETTINGS)


def configure_guarded_alembic_database_environment(
    environment: MutableMapping[str, str] | None = None,
) -> str:
    """Select only a fail-closed, explicitly approved Alembic target."""
    target_environment = environment if environment is not None else os.environ
    target_name = target_environment.get("AI_BAP_ALEMBIC_TARGET")

    if target_name in (None, "isolated-test"):
        configure_test_database_environment(target_environment)
        return "isolated-test"

    if target_name == LEGACY_MIGRATION_TEST_TARGET:
        configure_legacy_migration_test_database_environment(target_environment)
        return LEGACY_MIGRATION_TEST_TARGET

    raise IntegrationDatabaseSafetyError("Alembic target selector is not approved.")


def validate_effective_test_database_target(
    database_url: Any,
    target_name: str = "isolated-test",
) -> None:
    """Reject an Alembic target outside the approved isolated database tuple."""
    expected_settings = TEST_DATABASE_SETTINGS
    if target_name == LEGACY_MIGRATION_TEST_TARGET:
        expected_settings = LEGACY_MIGRATION_TEST_DATABASE_SETTINGS
    elif target_name != "isolated-test":
        raise IntegrationDatabaseSafetyError("Alembic target selector is not approved.")

    expected_target = {
        "host": expected_settings["POSTGRES_HOST"],
        "port": int(expected_settings["POSTGRES_PORT"]),
        "database": expected_settings["POSTGRES_DB"],
        "username": expected_settings["POSTGRES_USER"],
    }
    actual_target = {
        "host": database_url.host,
        "port": database_url.port,
        "database": database_url.database,
        "username": database_url.username,
    }

    if actual_target != expected_target:
        raise IntegrationDatabaseSafetyError(
            "Alembic target must be the isolated PostgreSQL test database."
        )
