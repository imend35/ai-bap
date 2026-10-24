
"""I test user registration and its security requirements."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings, get_settings
from app.database import SessionLocal, get_db
from app.main import app
from app.models.user import User
from app.password_service import hash_password, verify_password
from app.routers import auth as auth_router


@pytest.fixture
def registration_enabled(monkeypatch: pytest.MonkeyPatch):
    """I opt into public registration for this test only."""
    monkeypatch.setenv("PUBLIC_REGISTRATION_ENABLED", "true")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def fake_database():
    """I provide a database double that records route side effects."""

    class FakeDatabase:
        def __init__(self) -> None:
            self.scalar_calls = 0
            self.add_calls = 0
            self.commit_calls = 0
            self.user: User | None = None
            self.pending_user: User | None = None

        def scalar(self, _statement):
            self.scalar_calls += 1
            return self.user

        def add(self, instance: User) -> None:
            self.add_calls += 1
            self.pending_user = instance

        def commit(self) -> None:
            self.commit_calls += 1
            if self.pending_user is not None:
                self.pending_user.id = self.pending_user.id or uuid4()
                self.pending_user.record_number = "USR-999"
                self.user = self.pending_user

        def refresh(self, _instance) -> None:
            return None

    database = FakeDatabase()

    def override_database():
        return database

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_database
    try:
        yield database
    finally:
        if previous_override is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous_override


def test_public_registration_is_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """I default registration to off when no environment override exists."""
    monkeypatch.delenv("PUBLIC_REGISTRATION_ENABLED", raising=False)

    settings = Settings(
        _env_file=None,
        jwt_secret_key="synthetic-settings-test-secret-value-000000",
    )

    assert settings.public_registration_enabled is False


def test_disabled_registration_returns_403_without_side_effects(
    monkeypatch: pytest.MonkeyPatch,
    fake_database,
) -> None:
    """I reject registration before querying, hashing, or persisting a user."""
    monkeypatch.setenv("PUBLIC_REGISTRATION_ENABLED", "false")
    get_settings.cache_clear()
    monkeypatch.setattr(
        auth_router,
        "hash_password",
        lambda _password: pytest.fail("Disabled registration must not hash passwords."),
    )
    monkeypatch.setattr(
        auth_router,
        "create_access_token",
        lambda _user_id: pytest.fail("Registration must not issue an access token."),
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "synthetic-disabled@example.com",
                    "full_name": "Synthetic Disabled User",
                    "password": "SyntheticTestPassword123!",
                },
            )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 403
    assert response.json() == {"detail": "Public registration is disabled."}
    assert "access_token" not in response.json()
    assert fake_database.scalar_calls == 0
    assert fake_database.add_calls == 0
    assert fake_database.commit_calls == 0


def test_existing_user_can_log_in_while_registration_is_disabled(
    monkeypatch: pytest.MonkeyPatch,
    fake_database,
) -> None:
    """I preserve login for a deliberately provisioned active account."""
    monkeypatch.setenv("PUBLIC_REGISTRATION_ENABLED", "false")
    get_settings.cache_clear()
    password = "SyntheticDemoPassword123!"
    fake_database.user = User(
        id=uuid4(),
        record_number="USR-999",
        email="synthetic-demo@example.com",
        full_name="Synthetic Demo User",
        password_hash=hash_password(password),
        role="business_analyst",
        is_active=True,
    )
    issued_tokens: list[str] = []
    monkeypatch.setattr(
        auth_router,
        "create_access_token",
        lambda user_id: issued_tokens.append(str(user_id)) or "synthetic-access-token",
    )

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/auth/login",
                json={
                    "email": "synthetic-demo@example.com",
                    "password": password,
                },
            )
    finally:
        get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "synthetic-access-token",
        "token_type": "bearer",
    }
    assert issued_tokens == [str(fake_database.user.id)]


def test_enabled_registration_preserves_contract_and_ignores_role_escalation(
    registration_enabled,
    fake_database,
) -> None:
    """I retain account creation while restricting public registration to BA."""
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "synthetic-enabled@example.com",
                "full_name": "Synthetic Enabled User",
                "password": "SyntheticTestPassword123!",
                "role": "admin",
            },
        )

    assert response.status_code == 201
    assert response.json()["role"] == "business_analyst"
    assert response.json()["is_active"] is True
    assert fake_database.add_calls == 1
    assert fake_database.commit_calls == 1
    assert fake_database.user is not None
    assert fake_database.user.role == "business_analyst"


def test_enabled_registration_preserves_duplicate_account_conflict(
    registration_enabled,
    fake_database,
) -> None:
    """I retain the duplicate-email response in enabled registration mode."""
    fake_database.user = User(
        id=uuid4(),
        record_number="USR-998",
        email="synthetic-existing@example.com",
        full_name="Synthetic Existing User",
        password_hash=hash_password("SyntheticExistingPassword123!"),
        role="business_analyst",
        is_active=True,
    )

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "synthetic-existing@example.com",
                "full_name": "Synthetic Duplicate User",
                "password": "SyntheticTestPassword123!",
            },
        )

    assert response.status_code == 409
    assert fake_database.add_calls == 0
    assert fake_database.commit_calls == 0


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


def test_register_user_successfully(registration_email, registration_enabled):
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


def test_duplicate_email_is_rejected(registration_email, registration_enabled):
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


def test_user_cannot_assign_admin_role(registration_email, registration_enabled):
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
