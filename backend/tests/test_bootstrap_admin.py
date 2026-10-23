"""I test the initial-administrator bootstrap logic without a database."""

from typing import Any, Self
from uuid import uuid4

import pytest
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError, ProgrammingError, SQLAlchemyError

from app.password_service import verify_password
from app.role_permissions import ADMIN
from scripts.bootstrap_admin import (
    BOOTSTRAP_ADMIN_ADVISORY_LOCK_KEY,
    BootstrapAdminResult,
    bootstrap_initial_admin,
    validate_bootstrap_details,
)


class FakeSession:
    """I model the small SQLAlchemy session surface used by bootstrap logic."""

    def __init__(
        self,
        scalar_results: list[Any] | None = None,
        commit_error: Exception | None = None,
        execute_error: Exception | None = None,
    ) -> None:
        self.scalar_results = iter(scalar_results or [])
        self.commit_error = commit_error
        self.execute_error = execute_error
        self.executed: list[tuple[Any, dict[str, Any]]] = []
        self.added: list[Any] = []
        self.commit_calls = 0
        self.rollback_calls = 0

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, statement: Any, parameters: dict[str, Any]) -> None:
        self.executed.append((statement, parameters))
        if self.execute_error is not None:
            raise self.execute_error

    def scalar(self, _: Any) -> Any:
        return next(self.scalar_results)

    def add(self, value: Any) -> None:
        self.added.append(value)

    def commit(self) -> None:
        self.commit_calls += 1
        if self.commit_error is not None:
            raise self.commit_error

    def rollback(self) -> None:
        self.rollback_calls += 1


def make_session_factory(session: FakeSession):
    """I return a session factory suitable for an isolated unit test."""

    return lambda: session


def test_validation_normalizes_email_and_full_name() -> None:
    """I apply the existing registration constraints to normalized input."""

    details = validate_bootstrap_details(
        "  ADMIN@Example.COM ",
        "  Initial Administrator  ",
        "TestPassword123!",
    )

    assert str(details.email) == "admin@example.com"
    assert details.full_name == "Initial Administrator"


def test_validation_accepts_the_isolated_bootstrap_fixture_email_shape() -> None:
    """I keep generated isolated bootstrap emails compatible with UserRegister."""

    email = f"bootstrap-{uuid4().hex}@example.com"

    details = validate_bootstrap_details(
        email,
        "Isolated Bootstrap Administrator",
        "IsolatedBootstrapPassword123!",
    )

    assert str(details.email) == email


def test_validation_rejects_existing_schema_violations() -> None:
    """I reject invalid email, name, and password values before database access."""

    with pytest.raises(ValidationError):
        validate_bootstrap_details("invalid-email", "A", "short")


def test_bootstrap_creates_hashed_active_admin_after_advisory_lock() -> None:
    """I create one active administrator only after protected checks pass."""

    session = FakeSession(scalar_results=[None, None])

    result = bootstrap_initial_admin(
        "  ADMIN@Example.COM ",
        "  Initial Administrator  ",
        "TestPassword123!",
        session_factory=make_session_factory(session),
    )

    assert result is BootstrapAdminResult.CREATED
    assert session.executed[0][1] == {"lock_key": BOOTSTRAP_ADMIN_ADVISORY_LOCK_KEY}
    assert "pg_advisory_xact_lock" in str(session.executed[0][0])
    assert session.commit_calls == 1
    assert session.rollback_calls == 0
    assert len(session.added) == 1

    admin = session.added[0]
    assert admin.email == "admin@example.com"
    assert admin.full_name == "Initial Administrator"
    assert admin.role == ADMIN
    assert admin.is_active is True
    assert admin.password_hash != "TestPassword123!"
    assert verify_password("TestPassword123!", admin.password_hash) is True


def test_bootstrap_rejects_duplicate_email_before_admin_check() -> None:
    """I reject an existing email and roll back without creating an account."""

    session = FakeSession(scalar_results=[object()])

    result = bootstrap_initial_admin(
        "admin@example.com",
        "Initial Administrator",
        "TestPassword123!",
        session_factory=make_session_factory(session),
    )

    assert result is BootstrapAdminResult.EMAIL_EXISTS
    assert session.added == []
    assert session.commit_calls == 0
    assert session.rollback_calls == 1


def test_bootstrap_rejects_when_an_active_admin_already_exists() -> None:
    """I preserve the existing active administrator and roll back the attempt."""

    session = FakeSession(scalar_results=[None, object()])

    result = bootstrap_initial_admin(
        "admin@example.com",
        "Initial Administrator",
        "TestPassword123!",
        session_factory=make_session_factory(session),
    )

    assert result is BootstrapAdminResult.ACTIVE_ADMIN_EXISTS
    assert session.added == []
    assert session.commit_calls == 0
    assert session.rollback_calls == 1


def test_bootstrap_rolls_back_integrity_error_without_exposing_it() -> None:
    """I safely handle a concurrent unique-email conflict during commit."""

    session = FakeSession(
        scalar_results=[None, None],
        commit_error=IntegrityError("INSERT", {}, Exception("duplicate")),
    )

    result = bootstrap_initial_admin(
        "admin@example.com",
        "Initial Administrator",
        "TestPassword123!",
        session_factory=make_session_factory(session),
    )

    assert result is BootstrapAdminResult.EMAIL_EXISTS
    assert session.rollback_calls == 1


def test_bootstrap_rolls_back_database_errors_without_database_details() -> None:
    """I convert database failures into a non-sensitive outcome."""

    session = FakeSession(execute_error=SQLAlchemyError("sensitive database detail"))

    result = bootstrap_initial_admin(
        "admin@example.com",
        "Initial Administrator",
        "TestPassword123!",
        session_factory=make_session_factory(session),
    )

    assert result is BootstrapAdminResult.FAILED
    assert session.rollback_calls == 1


def test_bootstrap_reports_only_safe_phase_and_error_category_for_test_diagnostics() -> None:
    """I retain a safe diagnostic category without retaining database details."""

    session = FakeSession(
        execute_error=ProgrammingError("SELECT", {}, Exception("sensitive detail")),
    )
    diagnostics: list[str] = []

    result = bootstrap_initial_admin(
        "admin@example.com",
        "Initial Administrator",
        "TestPassword123!",
        session_factory=make_session_factory(session),
        diagnostic_reporter=diagnostics.append,
    )

    assert result is BootstrapAdminResult.FAILED
    assert diagnostics == ["advisory_lock:programming_error"]
    assert "sensitive detail" not in diagnostics
