"""Run a serialized, non-destructive Alembic upgrade before deployment."""

from __future__ import annotations

import subprocess

import psycopg

from app.config import get_settings

MIGRATION_ADVISORY_LOCK_KEY = 8_108_400_001


def main() -> int:
    """Acquire a database-wide lock and upgrade the configured schema to head."""
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
            print("Applying Alembic migrations with the deployment advisory lock.")
            subprocess.run(["alembic", "upgrade", "head"], check=True)
        finally:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_unlock(%s)",
                    (MIGRATION_ADVISORY_LOCK_KEY,),
                )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
