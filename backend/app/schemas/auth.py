
"""I define request and response schemas for user authentication."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """I validate the information required to register a user."""

    email: EmailStr
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=12, max_length=128)


class UserLogin(BaseModel):
    """I validate user login credentials."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """I return public user information without exposing password hashes."""

    id: UUID
    email: EmailStr
    full_name: str
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """I return a JWT access token after successful authentication."""

    access_token: str
    token_type: str = "bearer"
