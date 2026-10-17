"""I test administrator user-creation schema validation."""

import pytest
from pydantic import ValidationError

from app.schemas.admin_user import AdminUserCreate


def test_admin_user_create_normalizes_email_and_full_name_before_validation():
    """I normalize account identifiers while preserving the supplied password."""

    password = "  TestPassword123!  "
    payload = AdminUserCreate(
        email="  ADMIN@Example.COM ",
        full_name="  New Administrator  ",
        password=password,
    )

    assert str(payload.email) == "admin@example.com"
    assert payload.full_name == "New Administrator"
    assert payload.password == password
    assert payload.role == "business_analyst"
    assert payload.is_active is True


@pytest.mark.parametrize(
    "payload",
    [
        {
            "email": "valid@example.com",
            "full_name": " ",
            "password": "TestPassword123!",
        },
        {
            "email": "invalid-email",
            "full_name": "Valid Name",
            "password": "TestPassword123!",
        },
        {
            "email": "valid@example.com",
            "full_name": "Valid Name",
            "password": "short",
        },
        {
            "email": "valid@example.com",
            "full_name": "Valid Name",
            "password": "TestPassword123!",
            "role": "owner",
        },
        {
            "email": "valid@example.com",
            "full_name": "Valid Name",
            "password": "TestPassword123!",
            "unexpected": "value",
        },
    ],
)
def test_admin_user_create_rejects_invalid_or_unknown_input(payload):
    """I reject invalid details after normalization and unknown fields."""

    with pytest.raises(ValidationError):
        AdminUserCreate(**payload)
