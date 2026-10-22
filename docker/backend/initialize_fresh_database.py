"""Initialize an empty local Compose database without modifying an existing one."""

from __future__ import annotations

import os
import subprocess
import sys

import psycopg


def main() -> int:
    """Apply Alembic only when Compose connects to an empty public schema."""
    if os.environ.get("AI_BAP_INITIALIZE_FRESH_DATABASE", "").lower() != "true":
        print("Fresh-database initialization is disabled; no migration was applied.")
        return 0

    connection = psycopg.connect(
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"],
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_catalog.pg_tables
                    WHERE schemaname = 'public'
                )
                """
            )
            has_public_tables = cursor.fetchone()[0]

    if has_public_tables:
        print("Existing database detected; no migration was applied.")
        return 0

    print("Empty local Compose database detected; applying Alembic migrations.")
    subprocess.run(["alembic", "upgrade", "head"], check=True)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"Fresh-database initialization failed: {type(exc).__name__}", file=sys.stderr)
        raise
