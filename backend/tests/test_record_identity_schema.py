"""I statically verify the Phase 1 record identity schema design.

These checks intentionally do not import application settings or connect to a
database, so they are safe to run without using the configured application DB.
"""

from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
MODELS_ROOT = BACKEND_ROOT / "app" / "models"
MIGRATION = (
    BACKEND_ROOT
    / "migrations"
    / "versions"
    / "c7a8d9e0f1b2_add_readable_record_numbers_and_creators.py"
)
OPENAPI = BACKEND_ROOT.parent / "openapi.yaml"


def test_models_declare_database_generated_record_numbers() -> None:
    """I verify all requested entities declare immutable display identifiers."""
    for model_name in ("user.py", "project.py", "requirement.py", "user_story.py"):
        source = (MODELS_ROOT / model_name).read_text(encoding="utf-8")
        assert "record_number" in source
        assert "unique=True" in source
        assert "server_default=FetchedValue()" in source


def test_authored_models_declare_nullable_creator_links() -> None:
    """I verify authored records preserve unknown historical creators."""
    for model_name in ("project.py", "requirement.py", "user_story.py"):
        source = (MODELS_ROOT / model_name).read_text(encoding="utf-8")
        assert "created_by_id" in source
        assert 'ForeignKey("users.id", ondelete="SET NULL")' in source
        assert "nullable=True" in source


def test_migration_uses_postgresql_sequences_and_immutable_triggers() -> None:
    """I verify the migration defines the required database protections."""
    source = MIGRATION.read_text(encoding="utf-8")

    for prefix, sequence in (
        ("PRJ", "projects_record_number_seq"),
        ("REQ", "requirements_record_number_seq"),
        ("US", "user_stories_record_number_seq"),
        ("USR", "users_record_number_seq"),
    ):
        assert prefix in source
        assert sequence in source

    assert "ROW_NUMBER() OVER (ORDER BY created_at ASC, id ASC)" in source
    assert "SET LOCAL lock_timeout = '5s'" in source
    assert "LOCK TABLE users, projects, requirements, user_stories" in source
    assert "IN SHARE ROW EXCLUSIVE MODE" in source
    assert "IN ACCESS EXCLUSIVE MODE" not in source
    assert "CREATE TRIGGER trg_assign_" in source
    assert "CREATE TRIGGER trg_prevent_" in source
    assert "prevent_record_number_change" in source


def test_openapi_declares_readable_identifiers_and_nullable_creators() -> None:
    """I verify the contract exposes planned display-only identity fields."""
    source = OPENAPI.read_text(encoding="utf-8")

    assert "RecordCreator:" in source
    assert 'pattern: "^PRJ-[0-9]{3,}$"' in source
    assert 'pattern: "^REQ-[0-9]{3,}$"' in source
    assert 'pattern: "^US-[0-9]{3,}$"' in source
    assert 'pattern: "^USR-[0-9]{3,}$"' in source
    assert "created_by:" in source
    assert 'type: "null"' in source
