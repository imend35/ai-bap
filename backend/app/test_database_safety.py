"""I enforce fail-closed configuration for PostgreSQL integration tests."""

import os
from collections.abc import MutableMapping
from typing import Any

from pydantic import ValidationError
from pydantic_settings.exceptions import SettingsError
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

TEST_MODE_VALUE = "true"
TEST_CONFIRMATION_VALUE = "isolated-postgresql-acknowledged"
TEST_TARGET = "isolated-test"
DISPOSABLE_TEST_TARGET = "disposable-regression"
DISPOSABLE_TEST_CONFIRMATION_VALUE = (
    "disposable-regression-postgresql-acknowledged"
)
TEST_DATABASE_SETTINGS = {
    "POSTGRES_HOST": "127.0.0.1",
    "POSTGRES_PORT": "55432",
    "POSTGRES_DB": "ai_bap_test",
    "POSTGRES_USER": "ai_bap_test_user",
}
DISPOSABLE_TEST_DATABASE_SETTINGS = {
    "POSTGRES_HOST": "127.0.0.1",
    "POSTGRES_PORT": "55435",
    "POSTGRES_DB": "ai_bap_regression_20261024",
    "POSTGRES_USER": "ai_bap_regression_user_20261024",
}
DISPOSABLE_TEST_PASSWORD_VARIABLE = "AI_BAP_DISPOSABLE_TEST_POSTGRES_PASSWORD"
LEGACY_MIGRATION_TEST_TARGET = "legacy-migration"
LEGACY_MIGRATION_TEST_CONFIRMATION_VALUE = "legacy-migration-postgresql-acknowledged"
LEGACY_MIGRATION_TEST_DATABASE_SETTINGS = {
    "POSTGRES_HOST": "127.0.0.1",
    "POSTGRES_PORT": "55433",
    "POSTGRES_DB": "ai_bap_legacy_test",
    "POSTGRES_USER": "ai_bap_legacy_test_user",
}

_TARGET_CONFIGURATION = {
    TEST_TARGET: (
        TEST_DATABASE_SETTINGS,
        "AI_BAP_TEST_DATABASE_CONFIRMATION",
        TEST_CONFIRMATION_VALUE,
        "AI_BAP_TEST_POSTGRES_PASSWORD",
    ),
    DISPOSABLE_TEST_TARGET: (
        DISPOSABLE_TEST_DATABASE_SETTINGS,
        "AI_BAP_DISPOSABLE_TEST_DATABASE_CONFIRMATION",
        DISPOSABLE_TEST_CONFIRMATION_VALUE,
        DISPOSABLE_TEST_PASSWORD_VARIABLE,
    ),
    LEGACY_MIGRATION_TEST_TARGET: (
        LEGACY_MIGRATION_TEST_DATABASE_SETTINGS,
        "AI_BAP_LEGACY_TEST_DATABASE_CONFIRMATION",
        LEGACY_MIGRATION_TEST_CONFIRMATION_VALUE,
        "AI_BAP_LEGACY_TEST_POSTGRES_PASSWORD",
    ),
}


class IntegrationDatabaseSafetyError(RuntimeError):
    """I report an unsafe integration-test database configuration."""


def _environment(
    environment: MutableMapping[str, str] | None,
) -> MutableMapping[str, str]:
    return environment if environment is not None else os.environ


def _reject_other_target_secrets(
    environment: MutableMapping[str, str],
    selected_target: str,
) -> None:
    """I reject credentials or acknowledgments for a different target."""
    for target_name, (_, confirmation_name, _, password_name) in (
        _TARGET_CONFIGURATION.items()
    ):
        if target_name == selected_target:
            continue
        if confirmation_name in environment or password_name in environment:
            raise IntegrationDatabaseSafetyError(
                "Conflicting test database target configuration is not allowed."
            )


def _validate_target_configuration(
    environment: MutableMapping[str, str],
    target_name: str,
) -> dict[str, str]:
    """I validate one exact allowlisted target and return its tuple."""
    if target_name not in _TARGET_CONFIGURATION:
        raise IntegrationDatabaseSafetyError(
            "The selected integration-test database target is not approved."
        )

    settings, confirmation_name, expected_confirmation, password_name = (
        _TARGET_CONFIGURATION[target_name]
    )
    if environment.get("AI_BAP_TEST_MODE") != TEST_MODE_VALUE:
        raise IntegrationDatabaseSafetyError(
            "Integration tests require AI_BAP_TEST_MODE=true."
        )

    if environment.get(confirmation_name) != expected_confirmation:
        raise IntegrationDatabaseSafetyError(
            "The selected integration-test target requires its exact confirmation."
        )

    _reject_other_target_secrets(environment, target_name)

    if target_name == DISPOSABLE_TEST_TARGET:
        if environment.get("AI_BAP_TEST_TARGET") != DISPOSABLE_TEST_TARGET:
            raise IntegrationDatabaseSafetyError(
                "The disposable integration-test target must be explicitly selected."
            )
        alembic_target = environment.get("AI_BAP_ALEMBIC_TARGET")
        if alembic_target not in (None, DISPOSABLE_TEST_TARGET):
            raise IntegrationDatabaseSafetyError(
                "Mixed integration-test and Alembic targets are not allowed."
            )
    elif target_name == TEST_TARGET:
        if environment.get("AI_BAP_TEST_TARGET") not in (None, TEST_TARGET):
            raise IntegrationDatabaseSafetyError(
                "Mixed integration-test target selectors are not allowed."
            )
        alembic_target = environment.get("AI_BAP_ALEMBIC_TARGET")
        if alembic_target not in (None, TEST_TARGET):
            raise IntegrationDatabaseSafetyError(
                "Mixed integration-test and Alembic targets are not allowed."
            )
    else:
        if "AI_BAP_TEST_TARGET" in environment:
            raise IntegrationDatabaseSafetyError(
                "The legacy migration target cannot be combined with a pytest target."
            )
        if environment.get("AI_BAP_ALEMBIC_TARGET") != target_name:
            raise IntegrationDatabaseSafetyError(
                "Legacy migration validation requires its explicit target selector."
            )

    for setting_name, expected_value in settings.items():
        if environment.get(setting_name) != expected_value:
            raise IntegrationDatabaseSafetyError(
                f"{setting_name} does not match the approved test target."
            )

    test_password = environment.get(password_name)
    if not test_password or environment.get("POSTGRES_PASSWORD") != test_password:
        raise IntegrationDatabaseSafetyError(
            "The selected test password must be non-empty and match POSTGRES_PASSWORD."
        )

    database_url = environment.get("DATABASE_URL")
    if database_url:
        try:
            validate_effective_test_database_target(
                make_url(database_url), target_name
            )
        except Exception as exc:
            if isinstance(exc, IntegrationDatabaseSafetyError):
                raise
            raise IntegrationDatabaseSafetyError(
                "DATABASE_URL is malformed or does not match the approved test target."
            ) from None

    environment.update(settings)
    return settings


def configure_test_database_environment(
    environment: MutableMapping[str, str] | None = None,
) -> None:
    """Validate the existing regular test target for backward compatibility."""
    _validate_target_configuration(_environment(environment), TEST_TARGET)


def configure_disposable_test_database_environment(
    environment: MutableMapping[str, str] | None = None,
) -> None:
    """Validate the explicitly selected disposable regression target."""
    _validate_target_configuration(
        _environment(environment), DISPOSABLE_TEST_TARGET
    )


def configure_pytest_test_database_environment(
    environment: MutableMapping[str, str] | None = None,
) -> str:
    """Select exactly one allowlisted database for pytest, with no fallback."""
    target_environment = _environment(environment)
    target_name = target_environment.get("AI_BAP_TEST_TARGET", TEST_TARGET)
    if target_name == TEST_TARGET:
        configure_test_database_environment(target_environment)
        return TEST_TARGET
    if target_name == DISPOSABLE_TEST_TARGET:
        configure_disposable_test_database_environment(target_environment)
        return DISPOSABLE_TEST_TARGET
    raise IntegrationDatabaseSafetyError(
        "The selected integration-test database target is not approved."
    )


def configure_legacy_migration_test_database_environment(
    environment: MutableMapping[str, str] | None = None,
) -> None:
    """Validate the separately approved legacy-migration database target."""
    _validate_target_configuration(
        _environment(environment), LEGACY_MIGRATION_TEST_TARGET
    )


def configure_guarded_alembic_database_environment(
    environment: MutableMapping[str, str] | None = None,
) -> str:
    """Select only a fail-closed, explicitly approved Alembic target."""
    target_environment = _environment(environment)
    target_name = target_environment.get("AI_BAP_ALEMBIC_TARGET", TEST_TARGET)

    if target_name == TEST_TARGET:
        if target_environment.get("AI_BAP_TEST_TARGET") not in (None, TEST_TARGET):
            raise IntegrationDatabaseSafetyError(
                "Mixed integration-test and Alembic targets are not allowed."
            )
        configure_test_database_environment(target_environment)
        return TEST_TARGET
    if target_name == DISPOSABLE_TEST_TARGET:
        configure_disposable_test_database_environment(target_environment)
        return DISPOSABLE_TEST_TARGET
    if target_name == LEGACY_MIGRATION_TEST_TARGET:
        configure_legacy_migration_test_database_environment(target_environment)
        return LEGACY_MIGRATION_TEST_TARGET
    raise IntegrationDatabaseSafetyError(
        "The selected Alembic target is not approved."
    )


def validate_effective_test_database_target(
    database_url: Any,
    target_name: str = TEST_TARGET,
) -> None:
    """Reject an effective URL outside the selected exact test tuple."""
    if target_name not in _TARGET_CONFIGURATION:
        raise IntegrationDatabaseSafetyError(
            "The selected integration-test database target is not approved."
        )

    expected_settings = _TARGET_CONFIGURATION[target_name][0]
    expected_target = {
        "host": expected_settings["POSTGRES_HOST"],
        "port": int(expected_settings["POSTGRES_PORT"]),
        "database": expected_settings["POSTGRES_DB"],
        "username": expected_settings["POSTGRES_USER"],
    }
    try:
        actual_target = {
            "host": database_url.host,
            "port": database_url.port,
            "database": database_url.database,
            "username": database_url.username,
        }
        backend_name = database_url.get_backend_name()
    except (ArgumentError, AttributeError, TypeError, ValueError):
        raise IntegrationDatabaseSafetyError(
            "The effective database URL is malformed or incomplete."
        ) from None

    if backend_name != "postgresql" or actual_target != expected_target:
        raise IntegrationDatabaseSafetyError(
            "The effective database URL does not match the approved test target."
        )


def validate_effective_settings_database_target(
    settings: Any,
    target_name: str,
) -> None:
    """I validate Settings, including any process- or dotenv-sourced URL override."""
    try:
        database_url = settings.database_url
    except (
        ArgumentError,
        AttributeError,
        RuntimeError,
        SettingsError,
        TypeError,
        ValidationError,
        ValueError,
    ):
        raise IntegrationDatabaseSafetyError(
            "Effective database settings are malformed or incomplete."
        ) from None
    validate_effective_test_database_target(database_url, target_name)
