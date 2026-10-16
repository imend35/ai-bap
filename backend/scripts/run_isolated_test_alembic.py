"""I run Alembic only after validating the isolated test database target."""

import sys

from app.test_database_safety import (
    configure_guarded_alembic_database_environment,
    validate_effective_test_database_target,
)


def main(arguments: list[str] | None = None) -> None:
    """Validate test isolation before passing approved arguments to Alembic."""
    target_name = configure_guarded_alembic_database_environment()

    # I import settings only after environment validation has completed.
    from app.config import get_settings

    settings = get_settings()
    validate_effective_test_database_target(settings.database_url, target_name)

    # I import Alembic only after confirming the effective database target.
    from alembic.config import CommandLine

    CommandLine().main(arguments or sys.argv[1:])


if __name__ == "__main__":
    main()
