
"""I test JWT-based user identity and account security."""

from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.jwt_service import create_access_token
from app.main import app
from app.models.user import User
from app.security import get_current_user


@pytest.fixture
def registered_user():
    """I register a temporary user and clean up after each test."""
    email = f"security-test-{uuid4().hex}@example.com"
    password = "TestPassword123!"

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": email,
                    "full_name": "Security Test User",
                    "password": password,
                },
            )

        assert response.status_code == 201, response.text

        yield {
            "email": email,
            "password": password,
            "user_id": response.json()["id"],
        }

    finally:
        # I remove the temporary user if it still exists.
        with SessionLocal() as db:
            user = db.scalar(
                select(User).where(User.email == email)
            )

            if user is not None:
                db.delete(user)
                db.commit()


def make_credentials(token):
    """I prepare bearer credentials for authentication tests."""
    return HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=token,
    )


def test_valid_jwt_returns_correct_user(registered_user):
    """I verify that a valid JWT identifies its database user."""
    with TestClient(app) as client:
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": registered_user["email"],
                "password": registered_user["password"],
            },
        )

    assert login.status_code == 200, login.text

    credentials = make_credentials(
        login.json()["access_token"]
    )

    with SessionLocal() as db:
        user = get_current_user(
            credentials=credentials,
            db=db,
        )

        assert str(user.id) == registered_user["user_id"]
        assert user.email == registered_user["email"]
        assert user.is_active is True


def test_missing_bearer_token_is_rejected():
    """I verify that authentication requires a bearer token."""
    with SessionLocal() as db:
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(
                credentials=None,
                db=db,
            )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Missing bearer token."


def test_invalid_jwt_is_rejected():
    """I verify that an invalid JWT cannot authenticate."""
    credentials = make_credentials("invalid.jwt.token")

    with SessionLocal() as db:
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(
                credentials=credentials,
                db=db,
            )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid or expired access token."


def test_deleted_user_jwt_is_rejected():
    """I verify that deleting a user invalidates their access."""
    nonexistent_user_id = uuid4()

    # I create a correctly signed JWT for a nonexistent user.
    token = create_access_token(nonexistent_user_id)
    credentials = make_credentials(token)

    with SessionLocal() as db:
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(
                credentials=credentials,
                db=db,
            )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "User account not found."


def test_inactive_user_jwt_is_rejected(registered_user):
    """I verify that inactive users cannot reuse existing JWTs."""
    with TestClient(app) as client:
        login = client.post(
            "/api/v1/auth/login",
            json={
                "email": registered_user["email"],
                "password": registered_user["password"],
            },
        )

    assert login.status_code == 200, login.text

    credentials = make_credentials(
        login.json()["access_token"]
    )

    # I deactivate the user after obtaining the access token.
    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.email == registered_user["email"]
            )
        )

        assert user is not None
        user.is_active = False
        db.commit()

    with SessionLocal() as db:
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(
                credentials=credentials,
                db=db,
            )

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "User account is inactive."
