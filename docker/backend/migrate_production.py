"""Run a serialized, non-destructive Alembic upgrade before deployment."""

from __future__ import annotations

import subprocess
import sys

import psycopg

from app.config import get_settings

MIGRATION_ADVISORY_LOCK_KEY = 8_108_400_001
MIGRATION_FAILURE_MESSAGE = "Database migration failed; the API will not start."


def main() -> int:
    """Acquire a database-wide lock and upgrade the configured schema to head."""
    try:
        settings = get_settings()
        connection_url = settings.database_url.set(
            drivername="postgresql"
        ).render_as_string(hide_password=False)

        with psycopg.connect(connection_url, autocommit=True) as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_lock(%s)",
                    (MIGRATION_ADVISORY_LOCK_KEY,),
                )

            try:
                subprocess.run(
                    ["alembic", "upgrade", "head"],
                    check=True,
                    capture_output=True,
                )
            finally:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT pg_advisory_unlock(%s)",
                        (MIGRATION_ADVISORY_LOCK_KEY,),
                    )
        print("Alembic migrations applied successfully.")
    except Exception:  # noqa: BLE001 - deployment boundary must fail closed.
        print(MIGRATION_FAILURE_MESSAGE, file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
