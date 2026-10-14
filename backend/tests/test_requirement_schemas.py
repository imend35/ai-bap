
"""Test validation rules for requirement request schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.requirement import RequirementCreate, RequirementUpdate


def test_create_requirement_with_valid_data():
    """Verify that valid requirement data is accepted."""
    project_id = uuid4()

    requirement = RequirementCreate(
        project_id=project_id,
        title="User Authentication",
        description="Users must be able to sign in securely.",
        priority="high",
        status="draft",
    )

    assert requirement.project_id == project_id
    assert requirement.title == "User Authentication"
    assert requirement.priority.value == "high"
    assert requirement.status.value == "draft"


def test_create_requirement_with_default_values():
    """Verify that default priority and status values are applied."""
    requirement = RequirementCreate(
        project_id=uuid4(),
        title="Generate User Stories",
        description="The system must generate user stories.",
    )

    assert requirement.priority.value == "medium"
    assert requirement.status.value == "draft"


def test_create_requirement_without_project_id():
    """Verify that a project identifier is required."""
    with pytest.raises(ValidationError):
        RequirementCreate(
            title="Valid Requirement",
            description="A valid requirement description.",
        )


def test_create_requirement_with_empty_title():
    """Verify that an empty requirement title is rejected."""
    with pytest.raises(ValidationError):
        RequirementCreate(
            project_id=uuid4(),
            title="",
            description="A valid requirement description.",
        )


def test_create_requirement_with_long_title():
    """Verify that titles exceeding 160 characters are rejected."""
    with pytest.raises(ValidationError):
        RequirementCreate(
            project_id=uuid4(),
            title="A" * 161,
            description="A valid requirement description.",
        )


def test_create_requirement_with_empty_description():
    """Verify that an empty requirement description is rejected."""
    with pytest.raises(ValidationError):
        RequirementCreate(
            project_id=uuid4(),
            title="Valid Requirement",
            description="",
        )


def test_create_requirement_with_long_description():
    """Verify that descriptions exceeding 5000 characters are rejected."""
    with pytest.raises(ValidationError):
        RequirementCreate(
            project_id=uuid4(),
            title="Valid Requirement",
            description="A" * 5001,
        )


def test_create_requirement_with_invalid_priority():
    """Verify that unsupported priority values are rejected."""
    with pytest.raises(ValidationError):
        RequirementCreate(
            project_id=uuid4(),
            title="Valid Requirement",
            description="A valid requirement description.",
            priority="urgent",
        )


def test_create_requirement_with_invalid_status():
    """Verify that unsupported requirement statuses are rejected."""
    with pytest.raises(ValidationError):
        RequirementCreate(
            project_id=uuid4(),
            title="Valid Requirement",
            description="A valid requirement description.",
            status="completed",
        )


def test_create_requirement_with_extra_field():
    """Verify that unexpected request fields are rejected."""
    with pytest.raises(ValidationError):
        RequirementCreate(
            project_id=uuid4(),
            title="Valid Requirement",
            description="A valid requirement description.",
            unknown_field="unexpected",
        )


def test_update_requirement_with_valid_data():
    """Verify that a partial requirement update is accepted."""
    requirement = RequirementUpdate(priority="critical")

    assert requirement.priority.value == "critical"
    assert requirement.title is None


def test_update_requirement_with_empty_payload():
    """Verify that an empty update payload is rejected."""
    with pytest.raises(ValidationError):
        RequirementUpdate()


def test_update_requirement_with_null_title():
    """Verify that a null requirement title is rejected."""
    with pytest.raises(ValidationError):
        RequirementUpdate(title=None)


def test_update_requirement_with_null_priority():
    """Verify that a null requirement priority is rejected."""
    with pytest.raises(ValidationError):
        RequirementUpdate(priority=None)


def test_update_requirement_with_long_description():
    """Verify that an update description cannot exceed 5000 characters."""
    with pytest.raises(ValidationError):
        RequirementUpdate(description="A" * 5001)
