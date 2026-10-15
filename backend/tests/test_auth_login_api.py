
"""I test user login and JWT authentication security."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.jwt_service import verify_access_token
from app.main import app
from app.models.user import User


@pytest.fixture
def registered_user():
    """I register a temporary user and clean up after each test."""
    email = f"login-test-{uuid4().hex}@example.com"
    password = "TestPassword123!"

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "full_name": "Login Test User",
                "password": password,
            },
        )

    assert response.status_code == 201, response.text

    try:
        yield {
            "email": email,
            "password": password,
            "user_id": response.json()["id"],
        }
    finally:
        # I remove the temporary user from PostgreSQL.
        with SessionLocal() as db:
            user = db.scalar(
                select(User).where(User.email == email)
            )

            if user is not None:
                db.delete(user)
                db.commit()


def test_successful_login_returns_valid_jwt(registered_user):
    """I verify that valid credentials produce a signed JWT."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": registered_user["email"],
                "password": registered_user["password"],
            },
        )

    assert response.status_code == 200, response.text

    data = response.json()

    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)

    from uuid import UUID

    assert verify_access_token(data["access_token"]) == UUID(
        registered_user["user_id"]
    )


def test_wrong_password_is_rejected(registered_user):
    """I verify that incorrect credentials never produce a JWT."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": registered_user["email"],
                "password": "WrongPassword123!",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."
    assert "access_token" not in response.json()


def test_unknown_email_is_rejected():
    """I verify that an unknown email cannot authenticate."""
    email = f"unknown-{uuid4().hex}@example.com"

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": email,
                "password": "TestPassword123!",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password."
    assert "access_token" not in response.json()


def test_inactive_user_is_rejected(registered_user):
    """I verify that inactive users cannot obtain access tokens."""
    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(
                User.email == registered_user["email"]
            )
        )

        assert user is not None
        user.is_active = False
        db.commit()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": registered_user["email"],
                "password": registered_user["password"],
            },
        )

    assert response.status_code == 403
    assert response.json()["detail"] == "User account is inactive."
    assert "access_token" not in response.json()
