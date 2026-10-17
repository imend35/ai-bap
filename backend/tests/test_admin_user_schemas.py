"""I test administrator user-creation schema validation."""

import pytest
from pydantic import ValidationError

from app.schemas.admin_user import AdminUserCreate, AdminUserUpdate


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


def test_admin_user_update_normalizes_full_name_and_tracks_supplied_fields():
    """I normalize the only mutable text field before validating a PATCH."""

    payload = AdminUserUpdate(full_name="  Updated Administrator  ")

    assert payload.full_name == "Updated Administrator"
    assert payload.model_fields_set == {"full_name"}


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"full_name": " "},
        {"full_name": None},
        {"role": None},
        {"role": "owner"},
        {"email": "unchanged@example.com"},
        {"is_active": False},
        {"password": "TestPassword123!"},
        {"record_number": "USR-001"},
    ],
)
def test_admin_user_update_rejects_empty_invalid_null_or_immutable_input(payload):
    """I allow only a non-empty, valid update of the approved fields."""

    with pytest.raises(ValidationError):
        AdminUserUpdate(**payload)
