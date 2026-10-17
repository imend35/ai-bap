"""Define schemas for administrator user management."""

from datetime import datetime
from typing import Literal
from unicodedata import normalize
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AdminUserCreate(BaseModel):
    """Validate an administrator's request to create a platform user."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(max_length=255)
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=12, max_length=128)
    role: Literal["admin", "business_analyst", "reviewer"] = "business_analyst"
    is_active: bool = True

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value: object) -> object:
        """Normalize an email address before email validation."""

        if isinstance(value, str):
            return normalize("NFC", value).strip().lower()

        return value

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, value: object) -> object:
        """Normalize a full name before length validation."""

        if isinstance(value, str):
            return normalize("NFC", value).strip()

        return value


class AdminUserResponse(BaseModel):
    """Represent a user returned to an authorized administrator."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    record_number: str = Field(pattern=r"^USR-[0-9]{3,}$")
    email: EmailStr
    full_name: str
    role: Literal["admin", "business_analyst", "reviewer"]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class AdminUserListResponse(BaseModel):
    """Represent a paginated administrator view of platform users."""

    items: list[AdminUserResponse]
    total: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
    offset: int = Field(ge=0)
