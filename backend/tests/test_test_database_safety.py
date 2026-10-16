"""I test the fail-closed integration-test database guard."""

import pytest
from types import SimpleNamespace

from app.test_database_safety import (
    LEGACY_MIGRATION_TEST_CONFIRMATION_VALUE,
    LEGACY_MIGRATION_TEST_DATABASE_SETTINGS,
    LEGACY_MIGRATION_TEST_TARGET,
    TEST_CONFIRMATION_VALUE,
    TEST_DATABASE_SETTINGS,
    TEST_MODE_VALUE,
    IntegrationDatabaseSafetyError,
    configure_guarded_alembic_database_environment,
    configure_legacy_migration_test_database_environment,
    configure_test_database_environment,
    validate_effective_test_database_target,
)


def safe_environment() -> dict[str, str]:
    """Return a complete, isolated test-database environment mapping."""
    return {
        "AI_BAP_TEST_MODE": TEST_MODE_VALUE,
        "AI_BAP_TEST_DATABASE_CONFIRMATION": TEST_CONFIRMATION_VALUE,
        "AI_BAP_TEST_POSTGRES_PASSWORD": "test-only-password",
        "POSTGRES_PASSWORD": "test-only-password",
        **TEST_DATABASE_SETTINGS,
    }


def safe_legacy_environment() -> dict[str, str]:
    """Return a complete, legacy migration validation environment mapping."""
    return {
        "AI_BAP_TEST_MODE": TEST_MODE_VALUE,
        "AI_BAP_ALEMBIC_TARGET": LEGACY_MIGRATION_TEST_TARGET,
        "AI_BAP_LEGACY_TEST_DATABASE_CONFIRMATION": (
            LEGACY_MIGRATION_TEST_CONFIRMATION_VALUE
        ),
        "AI_BAP_LEGACY_TEST_POSTGRES_PASSWORD": "legacy-test-only-password",
        "POSTGRES_PASSWORD": "legacy-test-only-password",
        **LEGACY_MIGRATION_TEST_DATABASE_SETTINGS,
    }


def test_guard_accepts_the_explicit_isolated_configuration() -> None:
    """I verify the expected test database settings are accepted."""
    environment = safe_environment()

    configure_test_database_environment(environment)

    assert environment["POSTGRES_HOST"] == "127.0.0.1"
    assert environment["POSTGRES_PORT"] == "55432"
    assert environment["POSTGRES_DB"] == "ai_bap_test"


@pytest.mark.parametrize(
    ("setting_name", "unsafe_value"),
    [
        ("AI_BAP_TEST_MODE", "false"),
        ("AI_BAP_TEST_DATABASE_CONFIRMATION", "not-confirmed"),
        ("POSTGRES_HOST", "database.example.test"),
        ("POSTGRES_PORT", "5433"),
        ("POSTGRES_DB", "ai_bap"),
        ("POSTGRES_USER", "ai_bap_user"),
        ("POSTGRES_PASSWORD", "different-password"),
    ],
)
def test_guard_rejects_unsafe_database_settings(
    setting_name: str,
    unsafe_value: str,
) -> None:
    """I verify unsafe mode, confirmation, and connection values fail closed."""
    environment = safe_environment()
    environment[setting_name] = unsafe_value

    with pytest.raises(IntegrationDatabaseSafetyError):
        configure_test_database_environment(environment)


def test_effective_target_accepts_the_isolated_database() -> None:
    """I verify the Alembic guard accepts only the expected URL target."""
    target = SimpleNamespace(
        host="127.0.0.1",
        port=55432,
        database="ai_bap_test",
        username="ai_bap_test_user",
    )

    validate_effective_test_database_target(target)


def test_legacy_guard_accepts_only_the_explicit_legacy_configuration() -> None:
    """I verify the legacy target needs its selector and separate confirmation."""
    environment = safe_legacy_environment()

    configure_legacy_migration_test_database_environment(environment)

    assert configure_guarded_alembic_database_environment(environment) == (
        LEGACY_MIGRATION_TEST_TARGET
    )
    assert environment["POSTGRES_PORT"] == "55433"
    assert environment["POSTGRES_DB"] == "ai_bap_legacy_test"


@pytest.mark.parametrize(
    ("setting_name", "unsafe_value"),
    [
        ("AI_BAP_ALEMBIC_TARGET", "isolated-test"),
        ("AI_BAP_LEGACY_TEST_DATABASE_CONFIRMATION", "not-confirmed"),
        ("POSTGRES_HOST", "database.example.test"),
        ("POSTGRES_PORT", "55432"),
        ("POSTGRES_DB", "ai_bap_test"),
        ("POSTGRES_USER", "ai_bap_test_user"),
        ("POSTGRES_PASSWORD", "different-password"),
    ],
)
def test_legacy_guard_rejects_unsafe_configuration(
    setting_name: str,
    unsafe_value: str,
) -> None:
    """I verify the legacy target also fails closed for every target setting."""
    environment = safe_legacy_environment()
    environment[setting_name] = unsafe_value

    with pytest.raises(IntegrationDatabaseSafetyError):
        configure_legacy_migration_test_database_environment(environment)


def test_effective_target_accepts_the_explicit_legacy_database() -> None:
    """I verify the URL guard accepts the approved legacy database tuple only."""
    target = SimpleNamespace(
        host="127.0.0.1",
        port=55433,
        database="ai_bap_legacy_test",
        username="ai_bap_legacy_test_user",
    )

    validate_effective_test_database_target(target, LEGACY_MIGRATION_TEST_TARGET)


def test_effective_target_rejects_a_primary_tuple_for_legacy_validation() -> None:
    """I verify the legacy URL guard cannot fall back to the ordinary test DB."""
    target = SimpleNamespace(
        host="127.0.0.1",
        port=55432,
        database="ai_bap_test",
        username="ai_bap_test_user",
    )

    with pytest.raises(IntegrationDatabaseSafetyError):
        validate_effective_test_database_target(
            target,
            LEGACY_MIGRATION_TEST_TARGET,
        )


@pytest.mark.parametrize(
    ("attribute", "unsafe_value"),
    [
        ("host", "localhost"),
        ("port", 5433),
        ("database", "ai_bap"),
        ("username", "ai_bap_user"),
    ],
)
def test_effective_target_rejects_any_application_database_value(
    attribute: str,
    unsafe_value: str | int,
) -> None:
    """I verify the Alembic guard rejects a target outside test isolation."""
    target = SimpleNamespace(
        host="127.0.0.1",
        port=55432,
        database="ai_bap_test",
        username="ai_bap_test_user",
    )
    setattr(target, attribute, unsafe_value)

    with pytest.raises(IntegrationDatabaseSafetyError):
        validate_effective_test_database_target(target)
