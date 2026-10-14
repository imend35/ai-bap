
import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.database import engine


@pytest.fixture(scope="module")
def database_connection():
    """Provide a real PostgreSQL connection for integration tests."""
    try:
        with engine.connect() as connection:
            yield connection
    except SQLAlchemyError as exc:
        pytest.fail(f"PostgreSQL connection failed: {exc}")


def test_database_connection(database_connection):
    """Verify that PostgreSQL executes a simple SQL query."""
    result = database_connection.execute(text("SELECT 1")).scalar_one()

    assert result == 1


def test_database_name(database_connection):
    """Verify that the connection uses the configured database."""
    expected_database = get_settings().postgres_db

    actual_database = database_connection.execute(
        text("SELECT current_database()")
    ).scalar_one()

    assert actual_database == expected_database


def test_database_user(database_connection):
    """Verify that the connection uses the configured database user."""
    expected_user = get_settings().postgres_user

    actual_user = database_connection.execute(
        text("SELECT current_user")
    ).scalar_one()

    assert actual_user == expected_user
