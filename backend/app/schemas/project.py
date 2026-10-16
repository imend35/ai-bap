
"""Define request and response schemas for project operations."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.record_creator import RecordCreator


class ProjectStatus(str, Enum):
    """Define the supported project lifecycle statuses."""

    PLANNED = "planned"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"


class ProjectCreate(BaseModel):
    """Validate the payload used to create a project."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    status: ProjectStatus = ProjectStatus.PLANNED


class ProjectUpdate(BaseModel):
    """Validate the payload used to update a project."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    status: ProjectStatus | None = None

    @model_validator(mode="after")
    def validate_update_fields(self) -> "ProjectUpdate":
        """Require at least one supplied field and reject null required fields."""
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("Project name cannot be null.")

        if "status" in self.model_fields_set and self.status is None:
            raise ValueError("Project status cannot be null.")

        return self


class ProjectResponse(BaseModel):
    """Represent a project returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    record_number: str = Field(pattern=r"^PRJ-[0-9]{3,}$")
    created_by: RecordCreator | None
    name: str
    description: str | None = None
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    """Represent a paginated list of projects."""

    items: list[ProjectResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
