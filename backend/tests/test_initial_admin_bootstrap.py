"""I verify environment-backed bootstrap behavior without a database connection."""

from __future__ import annotations

import importlib.util
from collections.abc import Mapping
from pathlib import Path

import pytest

from app import initial_admin_bootstrap
from app.initial_admin_bootstrap import (
    INITIAL_ADMIN_BOOTSTRAP_ENABLED,
    INITIAL_ADMIN_EMAIL,
    INITIAL_ADMIN_FULL_NAME,
    INITIAL_ADMIN_PASSWORD,
    BootstrapAdminResult,
    EnvironmentBootstrapResult,
    bootstrap_initial_admin_from_environment,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BOOTSTRAP_LAUNCHER = (
    PROJECT_ROOT / "docker" / "backend" / "bootstrap_initial_admin_from_environment.py"
)


def load_bootstrap_launcher():
    """Load the container child process without executing it as a process."""
    specification = importlib.util.spec_from_file_location(
        "bootstrap_initial_admin_from_environment_for_test",
        BOOTSTRAP_LAUNCHER,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def enabled_environment(**overrides: str) -> dict[str, str]:
    """Provide non-sensitive valid-shaped values for adapter tests."""
    environment = {
        INITIAL_ADMIN_BOOTSTRAP_ENABLED: "true",
        INITIAL_ADMIN_EMAIL: "initial-admin@example.test",
        INITIAL_ADMIN_FULL_NAME: "Initial Administrator",
        INITIAL_ADMIN_PASSWORD: "BootstrapTestPassword123!",
    }
    environment.update(overrides)
    return environment


@pytest.mark.parametrize("flag", [None, "", "false", "True", "TRUE", " true"])
def test_environment_bootstrap_is_disabled_unless_flag_is_exactly_true(
    flag: str | None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """I require an exact explicit opt-in before reading administrator details."""
    called = False

    def unexpected_bootstrap(*_args: object, **_kwargs: object) -> BootstrapAdminResult:
        nonlocal called
        called = True
        return BootstrapAdminResult.CREATED

    monkeypatch.setattr(initial_admin_bootstrap, "bootstrap_initial_admin", unexpected_bootstrap)
    environment: dict[str, str] = {}
    if flag is not None:
        environment[INITIAL_ADMIN_BOOTSTRAP_ENABLED] = flag

    assert bootstrap_initial_admin_from_environment(environment) is EnvironmentBootstrapResult.DISABLED
    assert called is False


@pytest.mark.parametrize(
    "overrides",
    [
        {INITIAL_ADMIN_EMAIL: ""},
        {INITIAL_ADMIN_EMAIL: "   "},
        {INITIAL_ADMIN_FULL_NAME: ""},
        {INITIAL_ADMIN_FULL_NAME: "   "},
        {INITIAL_ADMIN_PASSWORD: ""},
        {INITIAL_ADMIN_PASSWORD: "   "},
    ],
)
def test_enabled_bootstrap_rejects_missing_or_blank_details_without_a_session(
    overrides: Mapping[str, str],
) -> None:
    """I fail closed before opening a session for incomplete configuration."""
    session_factory_called = False
    diagnostics: list[str] = []

    def unexpected_session_factory() -> object:
        nonlocal session_factory_called
        session_factory_called = True
        raise AssertionError("Incomplete bootstrap must not open a database session.")

    assert (
        bootstrap_initial_admin_from_environment(
            enabled_environment(**overrides),
            session_factory=unexpected_session_factory,
            diagnostic_reporter=diagnostics.append,
        )
        is EnvironmentBootstrapResult.FAILED
    )
    assert session_factory_called is False
    assert diagnostics == ["configuration:missing_required_details"]


@pytest.mark.parametrize(
    "overrides",
    [
        {INITIAL_ADMIN_EMAIL: "invalid-email"},
        {INITIAL_ADMIN_FULL_NAME: "A"},
        {INITIAL_ADMIN_PASSWORD: "too-short"},
    ],
)
def test_enabled_bootstrap_rejects_invalid_registration_details_without_a_session(
    overrides: Mapping[str, str],
) -> None:
    """I reuse registration validation before any database work begins."""
    session_factory_called = False
    diagnostics: list[str] = []

    def unexpected_session_factory() -> object:
        nonlocal session_factory_called
        session_factory_called = True
        raise AssertionError("Invalid bootstrap must not open a database session.")

    assert (
        bootstrap_initial_admin_from_environment(
            enabled_environment(**overrides),
            session_factory=unexpected_session_factory,
            diagnostic_reporter=diagnostics.append,
        )
        is EnvironmentBootstrapResult.FAILED
    )
    assert session_factory_called is False
    assert diagnostics == ["validation:invalid_registration_details"]


def test_environment_adapter_propagates_the_safe_diagnostic_reporter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """I pass the requested test reporter to the database bootstrap operation."""
    received_reporter: object | None = None
    diagnostics: list[str] = []
    reporter = diagnostics.append

    def stub_bootstrap(*_args: object, **kwargs: object) -> BootstrapAdminResult:
        nonlocal received_reporter
        received_reporter = kwargs["diagnostic_reporter"]
        assert callable(received_reporter)
        received_reporter("advisory_lock:operational_error")
        return BootstrapAdminResult.FAILED

    monkeypatch.setattr(initial_admin_bootstrap, "bootstrap_initial_admin", stub_bootstrap)

    assert (
        bootstrap_initial_admin_from_environment(
            enabled_environment(),
            session_factory=lambda: None,
            diagnostic_reporter=reporter,
        )
        is EnvironmentBootstrapResult.FAILED
    )
    assert callable(received_reporter)
    assert received_reporter is not reporter
    assert diagnostics == ["advisory_lock:operational_error"]


def test_environment_adapter_reports_a_safe_fallback_for_uncategorized_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """I prevent an empty test diagnostic list for a delegated failed result."""
    diagnostics: list[str] = []

    monkeypatch.setattr(
        initial_admin_bootstrap,
        "bootstrap_initial_admin",
        lambda *_args, **_kwargs: BootstrapAdminResult.FAILED,
    )

    assert (
        bootstrap_initial_admin_from_environment(
            enabled_environment(),
            session_factory=lambda: None,
            diagnostic_reporter=diagnostics.append,
        )
        is EnvironmentBootstrapResult.FAILED
    )
    assert diagnostics == ["bootstrap:failed_without_category"]


@pytest.mark.parametrize(
    ("bootstrap_result", "expected_result"),
    [
        (BootstrapAdminResult.CREATED, EnvironmentBootstrapResult.CREATED),
        (BootstrapAdminResult.ACTIVE_ADMIN_EXISTS, EnvironmentBootstrapResult.ACTIVE_ADMIN_EXISTS),
        (BootstrapAdminResult.EMAIL_EXISTS, EnvironmentBootstrapResult.EMAIL_EXISTS),
        (BootstrapAdminResult.FAILED, EnvironmentBootstrapResult.FAILED),
    ],
)
def test_environment_bootstrap_delegates_to_existing_secure_operation(
    bootstrap_result: BootstrapAdminResult,
    expected_result: EnvironmentBootstrapResult,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """I map the existing operation's outcomes without reimplementing its logic."""
    received: tuple[object, ...] | None = None

    def stub_bootstrap(*args: object, **kwargs: object) -> BootstrapAdminResult:
        nonlocal received
        received = (*args, kwargs["session_factory"])
        return bootstrap_result

    session_factory = lambda: None
    monkeypatch.setattr(initial_admin_bootstrap, "bootstrap_initial_admin", stub_bootstrap)

    assert (
        bootstrap_initial_admin_from_environment(
            enabled_environment(),
            session_factory=session_factory,
        )
        is expected_result
    )
    assert received == (
        "initial-admin@example.test",
        "Initial Administrator",
        "BootstrapTestPassword123!",
        session_factory,
    )


def test_environment_adapter_has_no_default_privileged_credentials() -> None:
    """I require operator-provided values rather than embedded administrator defaults."""
    source = initial_admin_bootstrap.__file__
    assert source is not None
    source_text = Path(source).read_text(encoding="utf-8")

    assert "AI_BAP_INITIAL_ADMIN_" in source_text
    assert "admin@example.com" not in source_text
    assert "Password123!" not in source_text


@pytest.mark.parametrize(
    "result",
    [
        EnvironmentBootstrapResult.DISABLED,
        EnvironmentBootstrapResult.CREATED,
        EnvironmentBootstrapResult.ACTIVE_ADMIN_EXISTS,
    ],
)
def test_bootstrap_launcher_accepts_safe_outcomes_without_output(
    result: EnvironmentBootstrapResult,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """I avoid outputting configuration values for successful or no-op outcomes."""
    launcher = load_bootstrap_launcher()
    monkeypatch.setattr(launcher, "bootstrap_initial_admin_from_environment", lambda: result)

    assert launcher.main() == 0
    assert capsys.readouterr().out == ""


def test_bootstrap_launcher_uses_generic_failure_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """I do not expose details when a configured bootstrap cannot complete."""
    launcher = load_bootstrap_launcher()
    monkeypatch.setattr(
        launcher,
        "bootstrap_initial_admin_from_environment",
        lambda: EnvironmentBootstrapResult.FAILED,
    )

    assert launcher.main() == 1
    assert capsys.readouterr().out == "Initial administrator bootstrap could not be completed.\n"


def test_bootstrap_launcher_hides_unexpected_failure_details(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """I do not expose an unexpected exception through startup process output."""
    launcher = load_bootstrap_launcher()
    monkeypatch.setattr(
        launcher,
        "bootstrap_initial_admin_from_environment",
        lambda: (_ for _ in ()).throw(Exception("synthetic-secret-like-value")),
    )

    assert launcher.main() == 1
    output = capsys.readouterr()
    assert output.out == "Initial administrator bootstrap could not be completed.\n"
    assert output.err == ""
    assert "synthetic-secret-like-value" not in output.out
    assert "synthetic-secret-like-value" not in output.err


def test_no_public_bootstrap_route_or_openapi_contract_exists() -> None:
    """I keep bootstrap inside startup code and outside the public API surface."""
    main_source = (PROJECT_ROOT / "backend" / "app" / "main.py").read_text(encoding="utf-8")
    contract = (PROJECT_ROOT / "openapi.yaml").read_text(encoding="utf-8")

    assert "bootstrap" not in main_source.lower()
    assert "bootstrap" not in contract.lower()
