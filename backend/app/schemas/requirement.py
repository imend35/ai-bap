
"""Define request and response schemas for requirement operations."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RequirementPriority(str, Enum):
    """Define the supported requirement priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RequirementStatus(str, Enum):
    """Define the supported requirement lifecycle statuses."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class RequirementCreate(BaseModel):
    """Validate the payload used to create a requirement."""

    model_config = ConfigDict(
    extra="forbid",
    json_schema_extra={"minProperties": 1},
)

    project_id: UUID
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=5000)
    priority: RequirementPriority = RequirementPriority.MEDIUM
    status: RequirementStatus = RequirementStatus.DRAFT


class RequirementUpdate(BaseModel):
    """Validate the payload used to update a requirement."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"minProperties": 1},
    )

    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = Field(
    default=None,
    min_length=1,
    max_length=5000,)
    priority: RequirementPriority | None = None
    status: RequirementStatus | None = None

    @model_validator(mode="after")
    def validate_update_fields(self) -> "RequirementUpdate":
        """Require at least one field and reject null required fields."""
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        for field_name in ("title", "description", "priority", "status"):
            if (
                field_name in self.model_fields_set
                and getattr(self, field_name) is None
            ):
                raise ValueError(f"{field_name} cannot be null.")

        return self


class RequirementResponse(BaseModel):
    """Represent a requirement returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    title: str
    description: str
    priority: RequirementPriority
    status: RequirementStatus
    created_at: datetime
    updated_at: datetime


class RequirementListResponse(BaseModel):
    """Represent a paginated list of requirements."""

    items: list[RequirementResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
