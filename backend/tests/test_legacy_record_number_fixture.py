"""Test the synthetic fixture contract for the record-number migration."""

import pytest

from app.test_database_safety import IntegrationDatabaseSafetyError
from scripts.seed_legacy_record_number_fixture import (
    APPROVAL_AUDITS,
    LEGACY_REVISION,
    PROJECTS,
    REQUIREMENTS,
    USER_STORIES,
    USERS,
    validate_legacy_revision,
)


def test_fixture_requires_the_expected_legacy_revision() -> None:
    """I verify the fixture cannot seed an unintended schema revision."""
    validate_legacy_revision(LEGACY_REVISION)

    with pytest.raises(IntegrationDatabaseSafetyError):
        validate_legacy_revision("c7a8d9e0f1b2")


@pytest.mark.parametrize(
    "fixture_rows",
    [USERS, PROJECTS, REQUIREMENTS, USER_STORIES, APPROVAL_AUDITS],
)
def test_fixture_has_two_rows_with_reverse_creation_order(fixture_rows: tuple[dict, ...]) -> None:
    """I verify backfill must order legacy rows rather than insertion order."""
    assert len(fixture_rows) == 2
    assert fixture_rows[0]["created_at"] > fixture_rows[1]["created_at"]


def test_fixture_preserves_legacy_foreign_keys_and_valid_statuses() -> None:
    """I verify the synthetic rows represent valid legacy business records."""
    assert {row["project_id"] for row in REQUIREMENTS} <= {
        row["id"] for row in PROJECTS
    }
    assert {row["requirement_id"] for row in USER_STORIES} <= {
        row["id"] for row in REQUIREMENTS
    }
    assert {row["user_story_id"] for row in APPROVAL_AUDITS} <= {
        row["id"] for row in USER_STORIES
    }
    assert {row["actor_id"] for row in APPROVAL_AUDITS} <= {row["id"] for row in USERS}
    assert {row["action"] for row in APPROVAL_AUDITS} == {"approved", "rejected"}
    assert all(row["new_status"] == row["action"] for row in APPROVAL_AUDITS)
