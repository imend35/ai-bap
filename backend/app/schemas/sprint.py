
"""Define request and response schemas for sprint operations."""

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class SprintStatus(str, Enum):
    """Define the supported sprint lifecycle statuses."""

    PLANNED = "planned"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"



class SprintCreate(BaseModel):
    """Validate the payload used to create a sprint."""

    model_config = ConfigDict(extra="forbid")

    project_id: UUID
    name: str = Field(min_length=1, max_length=160)
    start_date: date
    end_date: date
    status: SprintStatus = SprintStatus.PLANNED

    @model_validator(mode="after")
    def validate_date_range(self) -> "SprintCreate":
        """Ensure the sprint end date is not before its start date."""
        if self.end_date < self.start_date:
            raise ValueError(
                "Sprint end_date must be on or after start_date."
            )

        return self



class SprintUpdate(BaseModel):
    """Validate the payload used to update a sprint."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"minProperties": 1},
    )

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=160,
    )
    start_date: date | None = None
    end_date: date | None = None
    status: SprintStatus | None = None

    @model_validator(mode="after")
    def validate_update_fields(self) -> "SprintUpdate":
        """Require at least one field and reject explicit null values."""
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null.")

        if (
            self.start_date is not None
            and self.end_date is not None
            and self.end_date < self.start_date
        ):
            raise ValueError(
                "Sprint end_date must be on or after start_date."
            )

        return self


class SprintResponse(BaseModel):
    """Represent a sprint returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    name: str
    start_date: date
    end_date: date
    status: SprintStatus
    created_at: datetime
    updated_at: datetime


class SprintListResponse(BaseModel):
    """Represent a paginated list of sprints."""

    items: list[SprintResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
