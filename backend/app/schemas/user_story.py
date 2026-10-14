
"""Define request and response schemas for user story operations."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AcceptanceCriteriaValidation(BaseModel):
    """Provide shared validation for acceptance criteria."""

    @field_validator("acceptance_criteria", check_fields=False)
    @classmethod
    def validate_acceptance_criteria(cls, criteria: list[str]) -> list[str]:
        """Reject empty or excessively long acceptance criteria."""
        for criterion in criteria:
            if not criterion.strip():
                raise ValueError("Acceptance criteria cannot be blank.")
            if len(criterion) > 1000:
                raise ValueError(
                    "Each acceptance criterion must be at most 1000 characters."
                )

        return criteria


class UserStoryStatus(str, Enum):
    """Define the supported user story lifecycle statuses."""

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class UserStoryCreate(AcceptanceCriteriaValidation):
    """Validate the payload used to create a user story."""

    model_config = ConfigDict(extra="forbid")

    requirement_id: UUID
    title: str = Field(min_length=1, max_length=160)
    description: str = Field(min_length=1, max_length=5000)
    acceptance_criteria: list[str] = Field(
        default_factory=list,
        max_length=30,
    )

    status: UserStoryStatus = UserStoryStatus.DRAFT


class UserStoryUpdate(AcceptanceCriteriaValidation):
    """Validate the payload used to update a user story."""

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
        min_length=1,
        max_length=5000,
    )
    acceptance_criteria: list[str] | None = Field(
        default=None,
        max_length=30,
    )
    status: UserStoryStatus | None = None

    @model_validator(mode="after")
    def validate_update_fields(self) -> "UserStoryUpdate":
        """Require at least one field and reject explicit null values."""
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null.")

        return self


class UserStoryResponse(BaseModel):
    """Represent a user story returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    requirement_id: UUID
    title: str
    description: str
    acceptance_criteria: list[str]
    status: UserStoryStatus
    created_at: datetime
    updated_at: datetime


class UserStoryListResponse(BaseModel):
    """Represent a paginated list of user stories."""

    items: list[UserStoryResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1)
    offset: int = Field(ge=0)
