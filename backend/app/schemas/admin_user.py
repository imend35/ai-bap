"""Define response schemas for administrator user-management reads."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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
