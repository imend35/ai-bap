"""Create the first active administrator through an intentional local command."""

from __future__ import annotations

from collections.abc import Callable
from enum import Enum
from getpass import getpass

from pydantic import ValidationError
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.password_service import hash_password
from app.role_permissions import ADMIN
from app.schemas.auth import UserRegister

# I serialize initial-administrator checks without holding a table-wide lock.
BOOTSTRAP_ADMIN_ADVISORY_LOCK_KEY = 7_432_094_863_100


class BootstrapAdminResult(str, Enum):
    """Represent the safe, non-sensitive outcome of a bootstrap attempt."""

    CREATED = "created"
    ACTIVE_ADMIN_EXISTS = "active_admin_exists"
    EMAIL_EXISTS = "email_exists"
    FAILED = "failed"


SessionFactory = Callable[[], Session]


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
) -> BootstrapAdminResult:
    """Create one active administrator when no active administrator exists.

    I validate input before opening a database session. Within the transaction,
    I use a PostgreSQL transaction-scoped advisory lock so concurrent bootstrap
    commands cannot both pass the active-administrator check.
    """

    details = validate_bootstrap_details(email, full_name, password)
    normalized_email = str(details.email).strip().lower()

    with session_factory() as db:
        try:
            db.execute(
                text("SELECT pg_advisory_xact_lock(:lock_key)"),
                {"lock_key": BOOTSTRAP_ADMIN_ADVISORY_LOCK_KEY},
            )

            email_exists = db.scalar(
                select(User.id).where(User.email == normalized_email).limit(1)
            )
            if email_exists is not None:
                db.rollback()
                return BootstrapAdminResult.EMAIL_EXISTS

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
            db.commit()
            return BootstrapAdminResult.CREATED
        except IntegrityError:
            db.rollback()
            return BootstrapAdminResult.EMAIL_EXISTS
        except SQLAlchemyError:
            db.rollback()
            return BootstrapAdminResult.FAILED


def prompt_for_bootstrap_details() -> tuple[str, str, str] | None:
    """Collect initial-administrator details without echoing the password."""

    email = input("Administrator email: ")
    full_name = input("Administrator full name: ")
    password = getpass("Administrator password: ")
    password_confirmation = getpass("Confirm administrator password: ")

    if password != password_confirmation:
        return None

    return email, full_name, password


def main() -> int:
    """Run the intentionally interactive administrator bootstrap workflow."""

    details = prompt_for_bootstrap_details()
    if details is None:
        print("Bootstrap did not create an administrator.")
        return 1

    try:
        result = bootstrap_initial_admin(*details)
    except ValidationError:
        print("Bootstrap input does not meet the required account constraints.")
        return 1

    if result is BootstrapAdminResult.CREATED:
        print("Initial administrator created.")
        return 0

    if result is BootstrapAdminResult.ACTIVE_ADMIN_EXISTS:
        print("An active administrator already exists; no account was created.")
        return 1

    print("Bootstrap did not create an administrator.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
