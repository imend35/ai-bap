"""Seed deterministic legacy data for the record-number migration test."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import Engine, text

from app.test_database_safety import (
    LEGACY_MIGRATION_TEST_TARGET,
    IntegrationDatabaseSafetyError,
    configure_legacy_migration_test_database_environment,
    validate_effective_test_database_target,
)

LEGACY_REVISION = "921eeafe8be6"
FIXTURE_TIMESTAMP = datetime(2026, 10, 1, tzinfo=UTC)

USERS = (
    {
        "id": UUID("00000000-0000-0000-0000-000000000011"),
        "email": "legacy.analyst@example.test",
        "full_name": "Legacy Analyst",
        "role": "business_analyst",
        "created_at": FIXTURE_TIMESTAMP.replace(hour=9),
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000012"),
        "email": "legacy.reviewer@example.test",
        "full_name": "Legacy Reviewer",
        "role": "reviewer",
        "created_at": FIXTURE_TIMESTAMP.replace(hour=8),
    },
)

PROJECTS = (
    {
        "id": UUID("00000000-0000-0000-0000-000000000021"),
        "name": "Legacy Payments",
        "description": "Synthetic legacy project for migration validation.",
        "status": "active",
        "created_at": FIXTURE_TIMESTAMP.replace(hour=10),
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000022"),
        "name": "Legacy Reporting",
        "description": "Synthetic legacy project for migration validation.",
        "status": "planned",
        "created_at": FIXTURE_TIMESTAMP.replace(hour=9),
    },
)

REQUIREMENTS = (
    {
        "id": UUID("00000000-0000-0000-0000-000000000031"),
        "project_id": PROJECTS[0]["id"],
        "title": "Capture payment status",
        "description": "The platform records a payment status.",
        "priority": "high",
        "status": "approved",
        "created_at": FIXTURE_TIMESTAMP.replace(hour=11),
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000032"),
        "project_id": PROJECTS[1]["id"],
        "title": "Export reporting data",
        "description": "The platform exports reporting data.",
        "priority": "medium",
        "status": "in_review",
        "created_at": FIXTURE_TIMESTAMP.replace(hour=10),
    },
)

USER_STORIES = (
    {
        "id": UUID("00000000-0000-0000-0000-000000000041"),
        "requirement_id": REQUIREMENTS[0]["id"],
        "title": "Review payment status",
        "description": "As an analyst, I review payment status.",
        "status": "approved",
        "created_at": FIXTURE_TIMESTAMP.replace(hour=12),
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000042"),
        "requirement_id": REQUIREMENTS[1]["id"],
        "title": "Download a report",
        "description": "As a reviewer, I download a report.",
        "status": "rejected",
        "created_at": FIXTURE_TIMESTAMP.replace(hour=11),
    },
)

APPROVAL_AUDITS = (
    {
        "id": UUID("00000000-0000-0000-0000-000000000051"),
        "user_story_id": USER_STORIES[0]["id"],
        "actor_id": USERS[1]["id"],
        "user_story_id_snapshot": USER_STORIES[0]["id"],
        "actor_id_snapshot": USERS[1]["id"],
        "action": "approved",
        "previous_status": "in_review",
        "new_status": "approved",
        "created_at": FIXTURE_TIMESTAMP.replace(hour=13),
    },
    {
        "id": UUID("00000000-0000-0000-0000-000000000052"),
        "user_story_id": USER_STORIES[1]["id"],
        "actor_id": USERS[1]["id"],
        "user_story_id_snapshot": USER_STORIES[1]["id"],
        "actor_id_snapshot": USERS[1]["id"],
        "action": "rejected",
        "previous_status": "in_review",
        "new_status": "rejected",
        "created_at": FIXTURE_TIMESTAMP.replace(hour=12),
    },
)


def validate_legacy_revision(actual_revision: str | None) -> None:
    """Refuse to seed a schema other than the intended legacy revision."""
    if actual_revision != LEGACY_REVISION:
        raise IntegrationDatabaseSafetyError(
            "The legacy fixture requires database revision "
            f"{LEGACY_REVISION}, but found {actual_revision!r}."
        )


def require_empty_fixture_tables(engine: Engine) -> None:
    """Ensure record-number expectations cannot be contaminated by prior data."""
    table_names = (
        "users",
        "projects",
        "requirements",
        "user_stories",
        "user_story_approval_audits",
    )
    with engine.connect() as connection:
        for table_name in table_names:
            row_exists = connection.scalar(
                text(f"SELECT EXISTS (SELECT 1 FROM {table_name})")
            )
            if row_exists:
                raise IntegrationDatabaseSafetyError(
                    f"The legacy fixture requires an empty {table_name} table."
                )


def seed_fixture(engine: Engine) -> None:
    """Insert a compact, ordered legacy data set in one transaction."""
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO users (id, email, full_name, password_hash, role, created_at, updated_at)
                VALUES (:id, :email, :full_name, :password_hash, :role,
                        :created_at, :created_at)
                """
            ),
            [{**user, "password_hash": "fixture-only-not-a-password"} for user in USERS],
        )
        connection.execute(
            text(
                """
                INSERT INTO projects (id, name, description, status, created_at, updated_at)
                VALUES (:id, :name, :description, :status, :created_at, :created_at)
                """
            ),
            PROJECTS,
        )
        connection.execute(
            text(
                """
                INSERT INTO requirements
                    (id, project_id, title, description, priority, status, created_at, updated_at)
                VALUES (:id, :project_id, :title, :description, :priority, :status,
                        :created_at, :created_at)
                """
            ),
            REQUIREMENTS,
        )
        connection.execute(
            text(
                """
                INSERT INTO user_stories
                    (id, requirement_id, title, description, acceptance_criteria, status,
                     created_at, updated_at)
                VALUES (:id, :requirement_id, :title, :description,
                        CAST('["Fixture criterion"]' AS jsonb), :status, :created_at,
                        :created_at)
                """
            ),
            USER_STORIES,
        )
        connection.execute(
            text(
                """
                INSERT INTO user_story_approval_audits
                    (id, user_story_id, actor_id, user_story_id_snapshot,
                     actor_id_snapshot, action, previous_status, new_status, created_at)
                VALUES (:id, :user_story_id, :actor_id, :user_story_id_snapshot,
                        :actor_id_snapshot, :action, :previous_status, :new_status,
                        :created_at)
                """
            ),
            APPROVAL_AUDITS,
        )


def main() -> None:
    """Validate the isolated target and seed its next-migration fixture."""
    configure_legacy_migration_test_database_environment()

    from sqlalchemy import create_engine

    from app.config import get_settings

    settings = get_settings()
    validate_effective_test_database_target(
        settings.database_url,
        LEGACY_MIGRATION_TEST_TARGET,
    )
    engine = create_engine(settings.database_url)

    with engine.connect() as connection:
        validate_legacy_revision(
            connection.scalar(text("SELECT version_num FROM alembic_version"))
        )

    require_empty_fixture_tables(engine)
    seed_fixture(engine)
    print("Seeded the synthetic legacy record-number fixture.")


if __name__ == "__main__":
    main()
