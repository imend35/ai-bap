
"""I test user registration and its security requirements."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app
from app.models.user import User
from app.password_service import verify_password


@pytest.fixture
def registration_email():
    """I provide a unique email and clean up the test user."""
    email = f"auth-test-{uuid4().hex}@example.com"

    try:
        yield email
    finally:
        with SessionLocal() as db:
            user = db.scalar(
                select(User).where(User.email == email)
            )

            if user is not None:
                db.delete(user)
                db.commit()


def test_register_user_successfully(registration_email):
    """I verify successful registration and secure password storage."""
    payload = {
        "email": registration_email,
        "full_name": "Registration Test User",
        "password": "TestPassword123!",
    }

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/register",
            json=payload,
        )

    assert response.status_code == 201, response.text

    data = response.json()

    assert data["email"] == registration_email
    assert data["full_name"] == payload["full_name"]
    assert data["role"] == "business_analyst"
    assert data["is_active"] is True
    assert "password_hash" not in data
    assert "password" not in data

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == registration_email)
        )

        assert user is not None
        assert user.password_hash != payload["password"]
        assert verify_password(
            payload["password"],
            user.password_hash,
        )


def test_duplicate_email_is_rejected(registration_email):
    """I verify that duplicate registrations are rejected."""
    payload = {
        "email": registration_email,
        "full_name": "Duplicate Test User",
        "password": "TestPassword123!",
    }

    with TestClient(app) as client:
        first_response = client.post(
            "/api/v1/auth/register",
            json=payload,
        )

        second_response = client.post(
            "/api/v1/auth/register",
            json=payload,
        )

    assert first_response.status_code == 201
    assert second_response.status_code == 409

    with SessionLocal() as db:
        users = db.scalars(
            select(User).where(User.email == registration_email)
        ).all()

        assert len(users) == 1


def test_invalid_email_is_rejected():
    """I verify that invalid email addresses are rejected."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "invalid-email",
                "full_name": "Invalid Email User",
                "password": "TestPassword123!",
            },
        )

    assert response.status_code == 422


def test_short_password_is_rejected(registration_email):
    """I verify that passwords below the minimum length are rejected."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": registration_email,
                "full_name": "Short Password User",
                "password": "short",
            },
        )

    assert response.status_code == 422


def test_user_cannot_assign_admin_role(registration_email):
    """I verify that registration cannot grant administrator access."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": registration_email,
                "full_name": "Role Security User",
                "password": "TestPassword123!",
                "role": "admin",
            },
        )

    assert response.status_code == 201, response.text
    assert response.json()["role"] == "business_analyst"

    with SessionLocal() as db:
        user = db.scalar(
            select(User).where(User.email == registration_email)
        )

        assert user is not None
        assert user.role == "business_analyst"
