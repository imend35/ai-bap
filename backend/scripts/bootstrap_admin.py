"""Create the first active administrator through an intentional local command."""

from __future__ import annotations

from getpass import getpass

from pydantic import ValidationError

from app.initial_admin_bootstrap import (
    BOOTSTRAP_ADMIN_ADVISORY_LOCK_KEY,
    BootstrapAdminResult,
    bootstrap_initial_admin,
    validate_bootstrap_details,
)

__all__ = [
    "BOOTSTRAP_ADMIN_ADVISORY_LOCK_KEY",
    "BootstrapAdminResult",
    "bootstrap_initial_admin",
    "main",
    "prompt_for_bootstrap_details",
    "validate_bootstrap_details",
]


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
