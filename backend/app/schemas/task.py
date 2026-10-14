
"""Define request and response schemas for task operations."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TaskStatus(str, Enum):
    """Define the supported task workflow statuses."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    IN_REVIEW = "in_review"
    DONE = "done"


class TaskCreate(BaseModel):
    """Validate the payload used to create a task."""

    model_config = ConfigDict(extra="forbid")

    story_id: UUID
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(default="", max_length=5000)
    status: TaskStatus = TaskStatus.TODO


class TaskUpdate(BaseModel):
    """Validate the payload used to update a task."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"minProperties": 1},
    )

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=160,
    )
    description: str | None = Field(
        default=None,
        max_length=5000,
    )
    status: TaskStatus | None = None

    @model_validator(mode="after")
    def validate_update_fields(self) -> "TaskUpdate":
        """Require at least one field and reject explicit null values."""
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null.")

        return self


class TaskResponse(BaseModel):
    """Represent a task returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    story_id: UUID
    title: str
    description: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    """Represent a paginated list of tasks."""

    items: list[TaskResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
