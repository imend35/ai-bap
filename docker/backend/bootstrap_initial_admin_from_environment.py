"""Run the explicit one-time administrator bootstrap without exposing values."""

from __future__ import annotations

from app.initial_admin_bootstrap import (
    EnvironmentBootstrapResult,
    bootstrap_initial_admin_from_environment,
)


def main() -> int:
    """Return a safe process result for the Free startup wrapper."""
    try:
        result = bootstrap_initial_admin_from_environment()
    except (RuntimeError, ValueError):
        print("Initial administrator bootstrap could not be completed.")
        return 1

    if result in (
        EnvironmentBootstrapResult.DISABLED,
        EnvironmentBootstrapResult.CREATED,
        EnvironmentBootstrapResult.ACTIVE_ADMIN_EXISTS,
    ):
        return 0

    print("Initial administrator bootstrap could not be completed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
