
"""I test JWT authentication and active-user security checks."""

from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.security import get_current_user


class FakeDatabase:
    """I simulate database user lookups without changing PostgreSQL."""

    def __init__(self, user=None):
        self.user = user
        self.requested_user_id = None

    def get(self, model, user_id):
        """I return the configured user for a database lookup."""
        self.requested_user_id = user_id
        return self.user


def make_credentials(token: str):
    """I prepare bearer credentials for authentication tests."""
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


def test_missing_jwt_is_rejected():
    """I verify that authentication requires a bearer token."""

    db = FakeDatabase()

    with pytest.raises(HTTPException) as exc_info:
        get_current_user(None, db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Missing bearer token."
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.parametrize(
    "token",
    [
        "invalid-jwt-token",
        "",
    ],
)
def test_invalid_jwt_is_rejected(token):
    """I verify that invalid JWT credentials are rejected."""

    db = FakeDatabase()

    with patch(
        "app.security.verify_access_token",
        return_value=None,
    ), pytest.raises(HTTPException) as exc_info:
        get_current_user(make_credentials(token), db)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Invalid or expired access token."
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


def test_expired_jwt_is_rejected():
    """I verify that an expired JWT cannot authenticate a user."""

    db = FakeDatabase()

    with patch(
        "app.security.verify_access_token",
        return_value=None,
    ) as mocked_verifier, pytest.raises(HTTPException) as exc_info:
        get_current_user(
            make_credentials("expired-jwt-token"),
            db,
        )

    mocked_verifier.assert_called_once_with("expired-jwt-token")

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Invalid or expired access token."


def test_missing_database_user_is_rejected():
    """I verify that JWT users must exist in PostgreSQL."""

    user_id = uuid4()
    db = FakeDatabase(user=None)

    with patch(
        "app.security.verify_access_token",
        return_value=user_id,
    ), pytest.raises(HTTPException) as exc_info:
        get_current_user(
            make_credentials("valid-test-jwt"),
            db,
        )

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "User account not found."
    assert db.requested_user_id == user_id


def test_inactive_user_is_rejected():
    """I verify that inactive users cannot access protected endpoints."""

    user_id = uuid4()
    user = SimpleNamespace(
        id=user_id,
        role="business_analyst",
        is_active=False,
    )
    db = FakeDatabase(user=user)

    with patch(
        "app.security.verify_access_token",
        return_value=user_id,
    ), pytest.raises(HTTPException) as exc_info:
        get_current_user(
            make_credentials("valid-test-jwt"),
            db,
        )

    assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
    assert exc_info.value.detail == "User account is inactive."


@pytest.mark.parametrize(
    "role",
    [
        "admin",
        "business_analyst",
        "reviewer",
    ],
)
def test_active_user_is_authenticated(role):
    """I verify that active users can authenticate with a valid JWT."""

    user_id = uuid4()
    user = SimpleNamespace(
        id=user_id,
        role=role,
        is_active=True,
    )
    db = FakeDatabase(user=user)

    with patch(
        "app.security.verify_access_token",
        return_value=user_id,
    ) as mocked_verifier:
        authenticated_user = get_current_user(
            make_credentials("valid-test-jwt"),
            db,
        )

    mocked_verifier.assert_called_once_with("valid-test-jwt")

    assert authenticated_user is user
    assert db.requested_user_id == user_id
    assert authenticated_user.role == role
