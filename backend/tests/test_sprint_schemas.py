
"""Test Sprint Pydantic schema validation."""

from datetime import date
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.sprint import SprintCreate, SprintStatus, SprintUpdate


def test_create_sprint_with_valid_dates():
    """Verify that a valid sprint date range is accepted."""
    project_id = uuid4()

    sprint = SprintCreate(
        project_id=project_id,
        name="Sprint 1",
        start_date=date(2026, 10, 20),
        end_date=date(2026, 11, 3),
    )

    assert sprint.project_id == project_id
    assert sprint.name == "Sprint 1"
    assert sprint.start_date == date(2026, 10, 20)
    assert sprint.end_date == date(2026, 11, 3)
    assert sprint.status == SprintStatus.PLANNED


def test_create_sprint_with_invalid_date_range():
    """Verify that a sprint cannot end before its start date."""
    with pytest.raises(
        ValidationError,
        match="Sprint end_date must be on or after start_date",
    ):
        SprintCreate(
            project_id=uuid4(),
            name="Invalid Sprint",
            start_date=date(2026, 10, 25),
            end_date=date(2026, 10, 20),
        )

def test_update_sprint_with_empty_payload():
    """Verify that a sprint update requires at least one field."""
    with pytest.raises(
        ValidationError,
        match="At least one field must be provided",
    ):
        SprintUpdate()

def test_update_sprint_with_null_name():
    """Verify that a sprint name cannot be explicitly set to null."""
    with pytest.raises(
        ValidationError,
        match="name cannot be null",
    ):
        SprintUpdate(name=None)

def test_update_sprint_with_invalid_date_range():
    """Verify that a sprint update rejects an invalid date range."""
    with pytest.raises(
        ValidationError,
        match="Sprint end_date must be on or after start_date",
    ):
        SprintUpdate(
            start_date=date(2026, 10, 25),
            end_date=date(2026, 10, 20),
        )

def test_create_sprint_with_invalid_status():
    """Verify that unsupported sprint statuses are rejected."""
    with pytest.raises(ValidationError):
        SprintCreate(
            project_id=uuid4(),
            name="Invalid Status Sprint",
            start_date=date(2026, 10, 20),
            end_date=date(2026, 11, 3),
            status="unknown",
        )

def test_create_sprint_with_long_name():
    """Verify that sprint names cannot exceed 160 characters."""
    with pytest.raises(ValidationError):
        SprintCreate(
            project_id=uuid4(),
            name="A" * 161,
            start_date=date(2026, 10, 20),
            end_date=date(2026, 11, 3),
        )

def test_create_sprint_with_empty_name():
    """Verify that a sprint name cannot be empty."""
    with pytest.raises(ValidationError):
        SprintCreate(
            project_id=uuid4(),
            name="",
            start_date=date(2026, 10, 20),
            end_date=date(2026, 11, 3),
        )
