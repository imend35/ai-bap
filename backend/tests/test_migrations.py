
"""Verify the database schema created by Alembic migrations."""

from sqlalchemy import inspect, text

from app.database import engine


def test_required_tables_exist():
    """Verify that the initial migration created the required tables."""
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())

    assert {"alembic_version", "projects", "requirements"} <= tables


def test_requirement_foreign_key():
    """Verify that requirements reference projects with cascade deletion."""
    inspector = inspect(engine)
    foreign_keys = inspector.get_foreign_keys("requirements")

    assert any(
        foreign_key["referred_table"] == "projects"
        and foreign_key["constrained_columns"] == ["project_id"]
        and foreign_key["referred_columns"] == ["id"]
        and foreign_key.get("options", {}).get("ondelete") == "CASCADE"
        for foreign_key in foreign_keys
    )


def test_postgresql_enum_values():
    """Verify that PostgreSQL enum values match the API specification."""
    expected_enums = {
        "project_status": [
            "planned",
            "active",
            "on_hold",
            "completed",
        ],
        "requirement_status": [
            "draft",
            "in_review",
            "approved",
            "rejected",
        ],
        "requirement_priority": [
            "low",
            "medium",
            "high",
            "critical",
        ],
    }

    query = text(
        """
        SELECT
            t.typname AS enum_name,
            e.enumlabel AS enum_value
        FROM pg_type AS t
        JOIN pg_enum AS e
            ON t.oid = e.enumtypid
        WHERE t.typname IN (
            'project_status',
            'requirement_status',
            'requirement_priority'
        )
        ORDER BY t.typname, e.enumsortorder
        """
    )

    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()

    actual_enums = {}

    for row in rows:
        actual_enums.setdefault(row["enum_name"], []).append(
            row["enum_value"]
        )

    assert actual_enums == expected_enums
