"""I test record identity response serialization without a database."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.auth import UserResponse
from app.schemas.project import ProjectResponse
from app.schemas.record_creator import RecordCreator
from app.schemas.requirement import RequirementResponse
from app.schemas.user_story import UserStoryResponse

CREATED_AT = datetime(2026, 10, 16, 12, 0, tzinfo=UTC)


def creator() -> SimpleNamespace:
    """I provide a creator relationship-shaped object."""
    return SimpleNamespace(
        record_number="USR-001",
        full_name="Ada Lovelace",
    )


@pytest.mark.parametrize(
    ("schema", "source", "record_number"),
    [
        (
            ProjectResponse,
            SimpleNamespace(
                id=uuid4(),
                record_number="PRJ-001",
                created_by=creator(),
                created_by_id=uuid4(),
                name="Identity Test Project",
                description="A project response.",
                status="planned",
                created_at=CREATED_AT,
                updated_at=CREATED_AT,
            ),
            "PRJ-001",
        ),
        (
            RequirementResponse,
            SimpleNamespace(
                id=uuid4(),
                record_number="REQ-001",
                created_by=creator(),
                created_by_id=uuid4(),
                project_id=uuid4(),
                title="Identity Test Requirement",
                description="A requirement response.",
                priority="high",
                status="draft",
                created_at=CREATED_AT,
                updated_at=CREATED_AT,
            ),
            "REQ-001",
        ),
        (
            UserStoryResponse,
            SimpleNamespace(
                id=uuid4(),
                record_number="US-001",
                created_by=creator(),
                created_by_id=uuid4(),
                requirement_id=uuid4(),
                title="Identity Test Story",
                description="A user story response.",
                acceptance_criteria=["Given a response, identity is visible."],
                status="draft",
                created_at=CREATED_AT,
                updated_at=CREATED_AT,
            ),
            "US-001",
        ),
    ],
)
def test_authored_responses_serialize_record_numbers_and_creators(
    schema: type[ProjectResponse | RequirementResponse | UserStoryResponse],
    source: SimpleNamespace,
    record_number: str,
) -> None:
    """I serialize relationship attributes without exposing creator UUIDs."""
    response = schema.model_validate(source)
    data = response.model_dump(mode="json")

    assert data["record_number"] == record_number
    assert data["created_by"] == {
        "record_number": "USR-001",
        "full_name": "Ada Lovelace",
    }
    assert "created_by_id" not in data


@pytest.mark.parametrize(
    ("schema", "source"),
    [
        (
            ProjectResponse,
            SimpleNamespace(
                id=uuid4(),
                record_number="PRJ-002",
                created_by=None,
                name="Legacy Project",
                description=None,
                status="planned",
                created_at=CREATED_AT,
                updated_at=CREATED_AT,
            ),
        ),
        (
            RequirementResponse,
            SimpleNamespace(
                id=uuid4(),
                record_number="REQ-002",
                created_by=None,
                project_id=uuid4(),
                title="Legacy Requirement",
                description="Creator ownership is unknown.",
                priority="medium",
                status="draft",
                created_at=CREATED_AT,
                updated_at=CREATED_AT,
            ),
        ),
        (
            UserStoryResponse,
            SimpleNamespace(
                id=uuid4(),
                record_number="US-002",
                created_by=None,
                requirement_id=uuid4(),
                title="Legacy Story",
                description="Creator ownership is unknown.",
                acceptance_criteria=[],
                status="draft",
                created_at=CREATED_AT,
                updated_at=CREATED_AT,
            ),
        ),
    ],
)
def test_authored_responses_preserve_null_historical_creators(
    schema: type[ProjectResponse | RequirementResponse | UserStoryResponse],
    source: SimpleNamespace,
) -> None:
    """I represent records without creator ownership as null."""
    assert schema.model_validate(source).created_by is None


def test_user_response_serializes_the_usr_record_number() -> None:
    """I expose a user's readable identifier without private attributes."""
    response = UserResponse.model_validate(
        SimpleNamespace(
            id=uuid4(),
            record_number="USR-002",
            email="ada@example.com",
            full_name="Ada Lovelace",
            role="business_analyst",
            is_active=True,
            password_hash="not-public",
        )
    )

    data = response.model_dump(mode="json")
    assert data["record_number"] == "USR-002"
    assert "password_hash" not in data


def test_record_creator_rejects_an_invalid_user_record_number() -> None:
    """I require the immutable USR display-number format."""
    with pytest.raises(ValidationError):
        RecordCreator(record_number="USR-invalid", full_name="Ada Lovelace")
