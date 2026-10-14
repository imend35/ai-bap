
"""Test bearer token authentication behavior."""

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.config import get_settings
from app.security import verify_demo_token


def test_valid_demo_token():
    """Verify that the configured demo token is accepted."""
    token = get_settings().demo_access_token.get_secret_value()

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )

    assert verify_demo_token(credentials) is None


def test_invalid_demo_token():
    """Verify that an incorrect demo token is rejected."""
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid-demo-token",
    )

    with pytest.raises(HTTPException) as exc_info:
        verify_demo_token(credentials)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Invalid bearer token."
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


def test_missing_demo_token():
    """Verify that requests without credentials are rejected."""
    with pytest.raises(HTTPException) as exc_info:
        verify_demo_token(None)

    assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc_info.value.detail == "Missing bearer token."
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}
