"""Provide reusable, one-time initial-administrator bootstrap operations."""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from enum import Enum

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError, ProgrammingError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.admin_user_lifecycle import (
    ACTIVE_ADMIN_LIFECYCLE_ADVISORY_LOCK_KEY,
    acquire_active_admin_lifecycle_lock,
)
from app.database import SessionLocal
from app.models.user import User
from app.password_service import hash_password
from app.role_permissions import ADMIN
from app.schemas.auth import UserRegister

INITIAL_ADMIN_BOOTSTRAP_ENABLED = "AI_BAP_INITIAL_ADMIN_BOOTSTRAP_ENABLED"
INITIAL_ADMIN_EMAIL = "AI_BAP_INITIAL_ADMIN_EMAIL"
INITIAL_ADMIN_FULL_NAME = "AI_BAP_INITIAL_ADMIN_FULL_NAME"
INITIAL_ADMIN_PASSWORD = "AI_BAP_INITIAL_ADMIN_PASSWORD"
INITIAL_ADMIN_ENVIRONMENT_VARIABLES = (
    INITIAL_ADMIN_EMAIL,
    INITIAL_ADMIN_FULL_NAME,
    INITIAL_ADMIN_PASSWORD,
)

# I retain this public constant for bootstrap callers while sharing its identity.
BOOTSTRAP_ADMIN_ADVISORY_LOCK_KEY = ACTIVE_ADMIN_LIFECYCLE_ADVISORY_LOCK_KEY


class BootstrapAdminResult(str, Enum):
    """Represent the safe, non-sensitive outcome of a bootstrap attempt."""

    CREATED = "created"
    ACTIVE_ADMIN_EXISTS = "active_admin_exists"
    EMAIL_EXISTS = "email_exists"
    FAILED = "failed"


class EnvironmentBootstrapResult(str, Enum):
    """Represent safe startup outcomes without exposing configured values."""

    DISABLED = "disabled"
    CREATED = "created"
    ACTIVE_ADMIN_EXISTS = "active_admin_exists"
    EMAIL_EXISTS = "email_exists"
    FAILED = "failed"


SessionFactory = Callable[[], Session]
DiagnosticReporter = Callable[[str], None]


def classify_sqlalchemy_error(error: SQLAlchemyError) -> str:
    """Return a test-safe error category without retaining exception details."""
    if isinstance(error, IntegrityError):
        return "integrity_error"
    if isinstance(error, OperationalError):
        return "operational_error"
    if isinstance(error, ProgrammingError):
        return "programming_error"
    return "sqlalchemy_error"


def report_diagnostic(
    diagnostic_reporter: DiagnosticReporter | None,
    event: str,
) -> None:
    """Emit a fixed, non-sensitive diagnostic event only when requested by tests."""
    if diagnostic_reporter is not None:
        diagnostic_reporter(event)


def validate_bootstrap_details(
    email: str,
    full_name: str,
    password: str,
) -> UserRegister:
    """Normalize operator input and apply the existing registration constraints."""
    return UserRegister(
        email=email.strip().lower(),
        full_name=full_name.strip(),
        password=password,
    )


def bootstrap_initial_admin(
    email: str,
    full_name: str,
    password: str,
    session_factory: SessionFactory = SessionLocal,
    diagnostic_reporter: DiagnosticReporter | None = None,
) -> BootstrapAdminResult:
    """Create one active administrator when no active administrator exists."""
    details = validate_bootstrap_details(email, full_name, password)
    normalized_email = str(details.email).strip().lower()

    with session_factory() as db:
        phase = "advisory_lock"
        try:
            acquire_active_admin_lifecycle_lock(db)

            phase = "email_lookup"
            email_exists = db.scalar(
                select(User.id).where(User.email == normalized_email).limit(1)
            )
            if email_exists is not None:
                db.rollback()
                return BootstrapAdminResult.EMAIL_EXISTS

            phase = "active_admin_lookup"
            active_admin_exists = db.scalar(
                select(User.id)
                .where(
                    User.role == ADMIN,
                    User.is_active.is_(True),
                )
                .limit(1)
            )
            if active_admin_exists is not None:
                db.rollback()
                return BootstrapAdminResult.ACTIVE_ADMIN_EXISTS

            admin = User(
                email=normalized_email,
                full_name=details.full_name,
                password_hash=hash_password(details.password),
                role=ADMIN,
                is_active=True,
            )
            db.add(admin)
            phase = "create_admin"
            db.commit()
            return BootstrapAdminResult.CREATED
        except IntegrityError as error:
            db.rollback()
            report_diagnostic(
                diagnostic_reporter,
                f"{phase}:{classify_sqlalchemy_error(error)}",
            )
            return BootstrapAdminResult.EMAIL_EXISTS
        except SQLAlchemyError as error:
            db.rollback()
            report_diagnostic(
                diagnostic_reporter,
                f"{phase}:{classify_sqlalchemy_error(error)}",
            )
            return BootstrapAdminResult.FAILED


def bootstrap_initial_admin_from_environment(
    environment: Mapping[str, str] | None = None,
    session_factory: SessionFactory = SessionLocal,
    diagnostic_reporter: DiagnosticReporter | None = None,
) -> EnvironmentBootstrapResult:
    """Bootstrap only after an explicit complete startup configuration."""
    configured_environment = environment if environment is not None else os.environ
    if configured_environment.get(INITIAL_ADMIN_BOOTSTRAP_ENABLED) != "true":
        return EnvironmentBootstrapResult.DISABLED

    email, full_name, password = (
        configured_environment.get(variable_name, "")
        for variable_name in INITIAL_ADMIN_ENVIRONMENT_VARIABLES
    )
    if not all(value.strip() for value in (email, full_name, password)):
        report_diagnostic(diagnostic_reporter, "configuration:missing_required_details")
        return EnvironmentBootstrapResult.FAILED

    diagnostic_reported = False

    def forward_diagnostic(event: str) -> None:
        """Track whether the delegated operation emitted a safe test event."""
        nonlocal diagnostic_reported
        diagnostic_reported = True
        report_diagnostic(diagnostic_reporter, event)

    try:
        if diagnostic_reporter is None:
            result = bootstrap_initial_admin(
                email,
                full_name,
                password,
                session_factory=session_factory,
            )
        else:
            result = bootstrap_initial_admin(
                email,
                full_name,
                password,
                session_factory=session_factory,
                diagnostic_reporter=forward_diagnostic,
            )
    except ValidationError:
        report_diagnostic(diagnostic_reporter, "validation:invalid_registration_details")
        return EnvironmentBootstrapResult.FAILED

    if result is BootstrapAdminResult.FAILED and not diagnostic_reported:
        report_diagnostic(diagnostic_reporter, "bootstrap:failed_without_category")

    return EnvironmentBootstrapResult(result.value)
