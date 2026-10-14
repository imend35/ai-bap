
"""Test validation rules for project API schemas."""

import pytest
from pydantic import ValidationError

from app.schemas import ProjectCreate, ProjectStatus, ProjectUpdate


def test_create_project_with_valid_data():
    """Verify that valid project data is accepted."""
    project = ProjectCreate(
        name="AI BAP Demo",
        description="Business analysis platform demo",
    )

    assert project.name == "AI BAP Demo"
    assert project.status == ProjectStatus.PLANNED


def test_create_project_with_invalid_status():
    """Verify that unsupported project statuses are rejected."""
    with pytest.raises(ValidationError):
        ProjectCreate.model_validate(
            {"name": "Demo", "status": "invalid"}
        )


def test_create_project_with_empty_name():
    """Verify that a project name cannot be empty."""
    with pytest.raises(ValidationError):
        ProjectCreate(name="")


def test_create_project_with_long_name():
    """Verify that project names cannot exceed 120 characters."""
    with pytest.raises(ValidationError):
        ProjectCreate(name="A" * 121)


def test_create_project_with_long_description():
    """Verify that descriptions cannot exceed 2000 characters."""
    with pytest.raises(ValidationError):
        ProjectCreate(
            name="Demo",
            description="A" * 2001,
        )


def test_update_project_with_empty_payload():
    """Verify that an update request must contain at least one field."""
    with pytest.raises(ValidationError):
        ProjectUpdate()


def test_update_project_with_null_name():
    """Verify that a project name cannot be explicitly set to null."""
    with pytest.raises(ValidationError):
        ProjectUpdate(name=None)


def test_update_project_with_valid_status():
    """Verify that a project status can be updated independently."""
    update = ProjectUpdate(status=ProjectStatus.ACTIVE)

    assert update.status == ProjectStatus.ACTIVE
    assert update.model_dump(exclude_unset=True) == {
        "status": ProjectStatus.ACTIVE
    }
