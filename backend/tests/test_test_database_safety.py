"""I test the fail-closed integration-test database guard."""

from types import SimpleNamespace

import pytest
from sqlalchemy.engine import make_url

from app.test_database_safety import (
    DISPOSABLE_TEST_CONFIRMATION_VALUE,
    DISPOSABLE_TEST_DATABASE_SETTINGS,
    DISPOSABLE_TEST_PASSWORD_VARIABLE,
    DISPOSABLE_TEST_TARGET,
    LEGACY_MIGRATION_TEST_CONFIRMATION_VALUE,
    LEGACY_MIGRATION_TEST_DATABASE_SETTINGS,
    LEGACY_MIGRATION_TEST_TARGET,
    TEST_CONFIRMATION_VALUE,
    TEST_DATABASE_SETTINGS,
    TEST_MODE_VALUE,
    IntegrationDatabaseSafetyError,
    configure_disposable_test_database_environment,
    configure_guarded_alembic_database_environment,
    configure_legacy_migration_test_database_environment,
    configure_pytest_test_database_environment,
    configure_test_database_environment,
    validate_effective_settings_database_target,
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


def safe_disposable_environment() -> dict[str, str]:
    """Return a complete synthetic disposable-target environment mapping."""
    password = "synthetic-disposable-test-password"
    return {
        "AI_BAP_TEST_MODE": TEST_MODE_VALUE,
        "AI_BAP_TEST_TARGET": DISPOSABLE_TEST_TARGET,
        "AI_BAP_DISPOSABLE_TEST_DATABASE_CONFIRMATION": (
            DISPOSABLE_TEST_CONFIRMATION_VALUE
        ),
        DISPOSABLE_TEST_PASSWORD_VARIABLE: password,
        "POSTGRES_PASSWORD": password,
        **DISPOSABLE_TEST_DATABASE_SETTINGS,
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
        get_backend_name=lambda: "postgresql",
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
    target = make_url(
        "postgresql+psycopg://ai_bap_legacy_test_user:synthetic@"
        "127.0.0.1:55433/ai_bap_legacy_test"
    )

    validate_effective_test_database_target(target, LEGACY_MIGRATION_TEST_TARGET)


def test_effective_target_rejects_a_primary_tuple_for_legacy_validation() -> None:
    """I verify the legacy URL guard cannot fall back to the ordinary test DB."""
    target = make_url(
        "postgresql+psycopg://ai_bap_test_user:synthetic@"
        "127.0.0.1:55432/ai_bap_test"
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
        get_backend_name=lambda: "postgresql",
    )
    setattr(target, attribute, unsafe_value)

    with pytest.raises(IntegrationDatabaseSafetyError):
        validate_effective_test_database_target(target)


def test_disposable_guard_accepts_complete_exact_configuration() -> None:
    environment = safe_disposable_environment()

    configure_pytest_test_database_environment(environment)

    assert environment["POSTGRES_HOST"] == "127.0.0.1"
    assert environment["POSTGRES_PORT"] == "55435"
    assert environment["POSTGRES_DB"] == "ai_bap_regression_20261024"
    assert environment["POSTGRES_USER"] == "ai_bap_regression_user_20261024"


def test_guarded_alembic_accepts_only_explicit_disposable_target() -> None:
    environment = safe_disposable_environment()
    environment["AI_BAP_ALEMBIC_TARGET"] = DISPOSABLE_TEST_TARGET

    assert configure_guarded_alembic_database_environment(environment) == (
        DISPOSABLE_TEST_TARGET
    )


def test_disposable_guard_rejects_missing_confirmation() -> None:
    environment = safe_disposable_environment()
    del environment["AI_BAP_DISPOSABLE_TEST_DATABASE_CONFIRMATION"]

    with pytest.raises(IntegrationDatabaseSafetyError):
        configure_disposable_test_database_environment(environment)


def test_disposable_guard_rejects_missing_test_mode_key() -> None:
    environment = safe_disposable_environment()
    del environment["AI_BAP_TEST_MODE"]

    with pytest.raises(IntegrationDatabaseSafetyError) as error:
        configure_pytest_test_database_environment(environment)

    assert "password" not in str(error.value).lower()
    assert environment["AI_BAP_TEST_TARGET"] == DISPOSABLE_TEST_TARGET


def test_disposable_guard_rejects_missing_password_key() -> None:
    environment = safe_disposable_environment()
    password = environment.pop(DISPOSABLE_TEST_PASSWORD_VARIABLE)

    with pytest.raises(IntegrationDatabaseSafetyError) as error:
        configure_pytest_test_database_environment(environment)

    assert password not in str(error.value)
    assert environment["AI_BAP_TEST_TARGET"] == DISPOSABLE_TEST_TARGET


def test_disposable_guard_rejects_previous_rubric_test_port() -> None:
    environment = safe_disposable_environment()
    environment["POSTGRES_PORT"] = "55434"

    with pytest.raises(IntegrationDatabaseSafetyError):
        configure_pytest_test_database_environment(environment)


@pytest.mark.parametrize(
    ("setting_name", "unsafe_value"),
    [
        ("AI_BAP_TEST_MODE", "false"),
        ("AI_BAP_DISPOSABLE_TEST_DATABASE_CONFIRMATION", "wrong-ack"),
        (DISPOSABLE_TEST_PASSWORD_VARIABLE, ""),
        ("POSTGRES_PASSWORD", "different-synthetic-password"),
        ("POSTGRES_HOST", "localhost"),
        ("POSTGRES_PORT", "55432"),
        ("POSTGRES_DB", "ai_bap_test"),
        ("POSTGRES_USER", "ai_bap_test_user"),
    ],
)
def test_disposable_guard_rejects_incomplete_or_wrong_values(
    setting_name: str,
    unsafe_value: str,
) -> None:
    environment = safe_disposable_environment()
    environment[setting_name] = unsafe_value

    with pytest.raises(IntegrationDatabaseSafetyError):
        configure_disposable_test_database_environment(environment)


@pytest.mark.parametrize(
    "environment_update",
    [
        {"AI_BAP_TEST_TARGET": "not-approved"},
        {"AI_BAP_ALEMBIC_TARGET": "legacy-migration"},
        {"AI_BAP_DISPOSABLE_TEST_DATABASE_CONFIRMATION": ""},
        {"AI_BAP_TEST_DATABASE_CONFIRMATION": TEST_CONFIRMATION_VALUE},
        {"AI_BAP_LEGACY_TEST_POSTGRES_PASSWORD": "synthetic-legacy"},
    ],
)
def test_disposable_guard_rejects_unknown_or_mixed_targets(
    environment_update: dict[str, str],
) -> None:
    environment = safe_disposable_environment()
    environment.update(environment_update)

    with pytest.raises(IntegrationDatabaseSafetyError):
        configure_pytest_test_database_environment(environment)


def test_disposable_guard_rejects_conflicting_database_url() -> None:
    environment = safe_disposable_environment()
    environment["DATABASE_URL"] = (
        "postgresql+psycopg://ai_bap_test_user:synthetic@127.0.0.1:55432/ai_bap_test"
    )

    with pytest.raises(IntegrationDatabaseSafetyError):
        configure_disposable_test_database_environment(environment)


def test_disposable_guard_rejects_malformed_database_url() -> None:
    environment = safe_disposable_environment()
    environment["DATABASE_URL"] = "not-a-database-url"

    with pytest.raises(IntegrationDatabaseSafetyError):
        configure_disposable_test_database_environment(environment)


def test_effective_settings_url_must_match_selected_target() -> None:
    settings = SimpleNamespace(
        database_url=make_url(
            "postgresql+psycopg://other:synthetic@"
            "127.0.0.1:55432/ai_bap_test"
        )
    )

    with pytest.raises(IntegrationDatabaseSafetyError):
        validate_effective_settings_database_target(
            settings, DISPOSABLE_TEST_TARGET
        )


def test_disposable_guard_error_does_not_disclose_password() -> None:
    environment = safe_disposable_environment()
    password = environment[DISPOSABLE_TEST_PASSWORD_VARIABLE]
    environment["POSTGRES_PASSWORD"] = "different-synthetic-password"

    with pytest.raises(IntegrationDatabaseSafetyError) as error:
        configure_disposable_test_database_environment(environment)

    assert password not in str(error.value)
    assert "different-synthetic-password" not in str(error.value)


def test_disposable_effective_url_matches_exact_target() -> None:
    target = make_url(
        "postgresql+psycopg://ai_bap_regression_user_20261024:synthetic@"
        "127.0.0.1:55435/ai_bap_regression_20261024"
    )

    validate_effective_test_database_target(target, DISPOSABLE_TEST_TARGET)
