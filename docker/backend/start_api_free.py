"""Run guarded migrations before replacing this process with the API server."""

from __future__ import annotations

import os
import subprocess
import sys

MIGRATION_SCRIPT = "/usr/local/bin/migrate_production.py"
INITIAL_ADMIN_BOOTSTRAP_SCRIPT = "/usr/local/bin/bootstrap_initial_admin_from_environment.py"
API_START_SCRIPT = "/usr/local/bin/start_api.py"


def run_required_startup_step(script: str, failure_message: str) -> int:
    """Run a required child step without exposing its configuration values."""
    try:
        subprocess.run([sys.executable, script], check=True)
    except subprocess.CalledProcessError as error:
        print(failure_message, file=sys.stderr)
        return error.returncode or 1
    except OSError:
        print(failure_message, file=sys.stderr)
        return 1
    return 0


def main() -> int:
    """Fail closed unless the advisory-locked migration completes successfully."""
    migration_result = run_required_startup_step(
        MIGRATION_SCRIPT,
        "Database migration failed; the API will not start.",
    )
    if migration_result != 0:
        return migration_result

    bootstrap_result = run_required_startup_step(
        INITIAL_ADMIN_BOOTSTRAP_SCRIPT,
        "Initial administrator bootstrap failed; the API will not start.",
    )
    if bootstrap_result != 0:
        return bootstrap_result

    try:
        os.execv(sys.executable, [sys.executable, API_START_SCRIPT])
    except OSError:
        print("API process could not be started after migration.", file=sys.stderr)
        return 1

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
