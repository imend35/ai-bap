"""Alembic environment dedicated to the clone-only rehearsal helper."""

import os
from pathlib import Path

from alembic import context
from sqlalchemy import URL, create_engine, pool

config = context.config
PASSWORD_FILE = Path("/run/secrets/restore_db_password")
EXPECTED_ENDPOINT = ("127.0.0.1", "5432", "restore_check_db")


def required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError("configuration_error")
    return value


def database_url() -> URL:
    """Build the clone-only URL without a password environment variable."""
    if not PASSWORD_FILE.is_file():
        raise RuntimeError("configuration_error")
    password = PASSWORD_FILE.read_text(encoding="utf-8").rstrip("\r\n")
    if not password:
        raise RuntimeError("configuration_error")
    endpoint = (required("REHEARSAL_DATABASE_HOST"), required("REHEARSAL_DATABASE_PORT"), required("REHEARSAL_DATABASE_NAME"))
    if endpoint != EXPECTED_ENDPOINT:
        raise RuntimeError("configuration_error")
    try:
        port = int(endpoint[1])
    except ValueError as error:
        raise RuntimeError("configuration_error") from error
    return URL.create("postgresql+psycopg", username=required("REHEARSAL_DATABASE_USER"), password=password, host=endpoint[0], port=port, database=endpoint[2])


def assert_clone_identity(connection) -> None:
    """Bind Alembic's own connection to the cluster checked immediately before it."""
    expected_oid = required("REHEARSAL_EXPECTED_DATABASE_OID")
    expected_system_identifier = required("REHEARSAL_EXPECTED_SYSTEM_IDENTIFIER")
    row = connection.exec_driver_sql(
        "SELECT current_database(), (SELECT oid FROM pg_database WHERE datname = current_database()), "
        "(pg_control_system()).system_identifier::text"
    ).one()
    if (
        row[0] != EXPECTED_ENDPOINT[2]
        or str(row[1]) != expected_oid
        or row[2] != expected_system_identifier
    ):
        raise RuntimeError("clone_identity_drift")


def run_migrations_offline() -> None:
    raise RuntimeError("offline_mode_not_supported")


def run_migrations_online() -> None:
    # Keep the password-bearing URL out of Alembic's Config object and logs.
    connectable = create_engine(database_url(), poolclass=pool.NullPool)
    with connectable.connect() as connection:
        assert_clone_identity(connection)
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
