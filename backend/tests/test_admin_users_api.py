"""I test administrator-only user-management read endpoints."""

from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from threading import Barrier, Thread
from uuid import UUID, uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.jwt_service import create_access_token
from app.main import app
from app.models.user import User
from app.password_service import verify_password
from app.role_permissions import ADMIN, BUSINESS_ANALYST, REVIEWER
from app.security import get_current_user

BASE_URL = "/api/v1/admin/users"
client = TestClient(app)


def create_user(
    db: Session,
    role: str = BUSINESS_ANALYST,
    is_active: bool = True,
    created_at: datetime | None = None,
    email: str | None = None,
) -> User:
    """Create an isolated test user without using public registration."""

    user = User(
        email=email or f"admin-users-{uuid4().hex}@example.com",
        full_name="Admin User API Test",
        password_hash="test-only-not-for-login",
        role=role,
        is_active=is_active,
    )
    if created_at is not None:
        user.created_at = created_at
        user.updated_at = created_at

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@contextmanager
def authenticated_as(role: str = ADMIN):
    """Provide an active authenticated user through the existing dependency."""

    with SessionLocal() as db:
        user = create_user(db, role=role)
        user_id = user.id

    app.dependency_overrides[get_current_user] = lambda: user

    try:
        yield client
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        with SessionLocal() as db:
            persisted_user = db.get(User, user_id)
            if persisted_user is not None:
                db.delete(persisted_user)
                db.commit()


@contextmanager
def temporary_users(*users: dict[str, object]):
    """Create and remove test-target users for an endpoint test."""

    user_ids: list[UUID] = []
    try:
        with SessionLocal() as db:
            for user_options in users:
                user = create_user(db, **user_options)
                user_ids.append(user.id)
            yield user_ids
    finally:
        with SessionLocal() as db:
            for user_id in user_ids:
                user = db.get(User, user_id)
                if user is not None:
                    db.delete(user)
            db.commit()


def test_admin_lists_users_with_safe_response_fields_and_inactive_accounts():
    """I include inactive accounts without returning credentials."""

    with temporary_users({"is_active": False}) as user_ids, authenticated_as() as api:
        response = api.get(BASE_URL, params={"limit": 100})

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    target = next(item for item in data["items"] if item["id"] == str(user_ids[0]))
    assert target["is_active"] is False
    assert UUID(target["id"]) == user_ids[0]
    assert target["record_number"].startswith("USR-")
    assert target["created_at"]
    assert target["updated_at"]
    assert {"password", "password_hash", "access_token", "token"}.isdisjoint(target)


def test_admin_creates_normalized_user_with_requested_role_and_safe_response():
    """I allow active administrators to create users without exposing credentials."""

    email = f"admin-create-{uuid4().hex}@example.com"
    payload = {
        "email": f"  {email.upper()}  ",
        "full_name": "  New Administrator  ",
        "password": "TestPassword123!",
        "role": ADMIN,
        "is_active": False,
    }

    try:
        with authenticated_as() as api:
            response = api.post(BASE_URL, json=payload)

        assert response.status_code == status.HTTP_201_CREATED, response.text
        data = response.json()
        assert data["email"] == email
        assert data["full_name"] == "New Administrator"
        assert data["role"] == ADMIN
        assert data["is_active"] is False
        assert data["record_number"].startswith("USR-")
        assert {"password", "password_hash", "access_token", "token"}.isdisjoint(data)

        with SessionLocal() as db:
            user = db.get(User, UUID(data["id"]))
            assert user is not None
            assert user.password_hash != payload["password"]
            assert verify_password(payload["password"], user.password_hash) is True
    finally:
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email))
            if user is not None:
                db.delete(user)
                db.commit()


def test_admin_create_defaults_to_active_business_analyst():
    """I apply the documented role and activation defaults."""

    email = f"admin-create-default-{uuid4().hex}@example.com"
    try:
        with authenticated_as() as api:
            response = api.post(
                BASE_URL,
                json={
                    "email": email,
                    "full_name": "Default User",
                    "password": "TestPassword123!",
                },
            )

        assert response.status_code == status.HTTP_201_CREATED, response.text
        assert response.json()["role"] == BUSINESS_ANALYST
        assert response.json()["is_active"] is True
    finally:
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email))
            if user is not None:
                db.delete(user)
                db.commit()


@pytest.mark.parametrize(
    "payload",
    [
        {
            "email": "not-an-email",
            "full_name": "Valid Name",
            "password": "TestPassword123!",
        },
        {
            "email": "invalid-name@example.com",
            "full_name": "  ",
            "password": "TestPassword123!",
        },
        {
            "email": "short-password@example.com",
            "full_name": "Valid Name",
            "password": "short",
        },
        {
            "email": "invalid-role@example.com",
            "full_name": "Valid Name",
            "password": "TestPassword123!",
            "role": "owner",
        },
        {
            "email": "unknown-field@example.com",
            "full_name": "Valid Name",
            "password": "TestPassword123!",
            "unexpected": "value",
        },
    ],
)
def test_admin_create_rejects_invalid_payloads(payload):
    """I validate normalized user details and reject unknown fields."""

    with authenticated_as() as api:
        response = api.post(BASE_URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_admin_create_rejects_duplicate_normalized_email():
    """I reject duplicate addresses after applying email normalization."""

    email = f"admin-create-duplicate-{uuid4().hex}@example.com"
    with temporary_users({"email": email}) as _user_ids, authenticated_as() as api:
        response = api.post(
            BASE_URL,
            json={
                "email": f"  {email.upper()}  ",
                "full_name": "Duplicate Account",
                "password": "TestPassword123!",
            },
        )

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "An account with this email already exists."


def test_admin_list_paginates_and_uses_deterministic_created_at_ordering():
    """I paginate an ordering based on creation timestamp and UUID."""

    now = datetime.now(UTC)
    with temporary_users(
        {"created_at": now - timedelta(days=2)},
        {"created_at": now - timedelta(days=1)},
        {"created_at": now},
    ) as user_ids, authenticated_as() as api:
        all_users = api.get(BASE_URL, params={"limit": 100})
        page = api.get(BASE_URL, params={"limit": 2, "offset": 1})

    assert all_users.status_code == status.HTTP_200_OK
    assert page.status_code == status.HTTP_200_OK
    all_data = all_users.json()
    page_data = page.json()
    all_ids = [item["id"] for item in all_data["items"]]
    assert all_ids.index(str(user_ids[2])) < all_ids.index(str(user_ids[1]))
    assert all_ids.index(str(user_ids[1])) < all_ids.index(str(user_ids[0]))
    assert page_data["items"] == all_data["items"][1:3]
    assert page_data["limit"] == 2
    assert page_data["offset"] == 1
    assert page_data["total"] == all_data["total"]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_admin_list_rejects_invalid_pagination(params):
    """I validate the list pagination bounds."""

    with authenticated_as() as api:
        response = api.get(BASE_URL, params=params)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_admin_gets_user_details_by_uuid_including_inactive_accounts():
    """I return the complete safe administrator response for a user."""

    with temporary_users(
        {"is_active": False, "role": REVIEWER}
    ) as user_ids, authenticated_as() as api:
        response = api.get(f"{BASE_URL}/{user_ids[0]}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(user_ids[0])
    assert response.json()["role"] == REVIEWER
    assert response.json()["is_active"] is False


def test_admin_user_detail_returns_not_found_for_unknown_user():
    """I return a controlled error for an unknown user identifier."""

    with authenticated_as() as api:
        response = api.get(f"{BASE_URL}/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User not found."


def test_admin_user_detail_rejects_malformed_uuid():
    """I delegate malformed UUID validation to FastAPI."""

    with authenticated_as() as api:
        response = api.get(f"{BASE_URL}/not-a-uuid")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_admin_updates_only_name_or_role_and_preserves_immutable_account_fields():
    """I permit partial administrator updates without changing account identity."""

    with temporary_users({"role": REVIEWER}) as user_ids, authenticated_as() as api:
        with SessionLocal() as db:
            target = db.get(User, user_ids[0])
            assert target is not None
            original = {
                "email": target.email,
                "password_hash": target.password_hash,
                "is_active": target.is_active,
                "record_number": target.record_number,
            }

        response = api.patch(
            f"{BASE_URL}/{user_ids[0]}",
            json={"full_name": "  Updated Reviewer  ", "role": BUSINESS_ANALYST},
        )

        assert response.status_code == status.HTTP_200_OK, response.text
        assert response.json()["full_name"] == "Updated Reviewer"
        assert response.json()["role"] == BUSINESS_ANALYST
        with SessionLocal() as db:
            target = db.get(User, user_ids[0])
            assert target is not None
            assert target.email == original["email"]
            assert target.password_hash == original["password_hash"]
            assert target.is_active is original["is_active"]
            assert target.record_number == original["record_number"]


def test_admin_update_accepts_valid_noop_and_rejects_invalid_payloads():
    """I return success for valid no-ops while retaining strict PATCH validation."""

    with temporary_users({"role": REVIEWER}) as user_ids, authenticated_as() as api:
        noop_response = api.patch(
            f"{BASE_URL}/{user_ids[0]}",
            json={"full_name": "Admin User API Test"},
        )
        empty_response = api.patch(f"{BASE_URL}/{user_ids[0]}", json={})
        immutable_response = api.patch(
            f"{BASE_URL}/{user_ids[0]}", json={"is_active": False}
        )

    assert noop_response.status_code == status.HTTP_200_OK
    assert empty_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert immutable_response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_admin_can_self_demote_when_another_active_admin_remains():
    """I allow self-demotion only while the active-admin set remains non-empty."""

    with temporary_users({"role": ADMIN}, {"role": ADMIN}) as user_ids:
        with SessionLocal() as db:
            actor = db.get(User, user_ids[0])
            assert actor is not None
        app.dependency_overrides[get_current_user] = lambda: actor
        try:
            response = client.patch(
                f"{BASE_URL}/{user_ids[0]}", json={"role": BUSINESS_ANALYST}
            )
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["role"] == BUSINESS_ANALYST


def test_admin_cannot_demote_the_last_active_admin():
    """I preserve the final active administrator, including self-demotion."""

    with temporary_users({"role": ADMIN}) as user_ids:
        with SessionLocal() as db:
            actor = db.get(User, user_ids[0])
            assert actor is not None
            active_admin_count = db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.role == ADMIN, User.is_active.is_(True))
            )
            assert active_admin_count == 1
        app.dependency_overrides[get_current_user] = lambda: actor
        try:
            response = client.patch(
                f"{BASE_URL}/{user_ids[0]}", json={"role": BUSINESS_ANALYST}
            )
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "The last active administrator cannot be demoted."


def test_concurrent_admin_demotions_leave_one_active_admin():
    """I serialize concurrent demotions so the active-admin set cannot reach zero."""

    with temporary_users({"role": ADMIN}, {"role": ADMIN}) as user_ids:
        with SessionLocal() as db:
            initial_active_admin_count = db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.role == ADMIN, User.is_active.is_(True))
            )
        assert initial_active_admin_count == 2

        start = Barrier(2)
        responses: list[int] = []

        def demote(user_id: UUID) -> None:
            headers = {"Authorization": f"Bearer {create_access_token(user_id)}"}
            with TestClient(app) as concurrent_client:
                start.wait()
                response = concurrent_client.patch(
                    f"{BASE_URL}/{user_id}",
                    json={"role": BUSINESS_ANALYST},
                    headers=headers,
                )
                responses.append(response.status_code)

        threads = [Thread(target=demote, args=(user_id,)) for user_id in user_ids]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        assert all(not thread.is_alive() for thread in threads)

        with SessionLocal() as db:
            active_admin_count = db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.role == ADMIN, User.is_active.is_(True))
            )

    assert sorted(responses) == [
        status.HTTP_200_OK,
        status.HTTP_409_CONFLICT,
    ]
    assert active_admin_count == 1


def test_admin_activation_and_deactivation_preserve_account_identity_fields():
    """I change only activation state and return the safe administrator schema."""

    with temporary_users({"is_active": False, "role": REVIEWER}) as user_ids:
        with SessionLocal() as db:
            target = db.get(User, user_ids[0])
            assert target is not None
            immutable_fields = {
                "id": target.id,
                "email": target.email,
                "password_hash": target.password_hash,
                "role": target.role,
                "record_number": target.record_number,
            }

        with authenticated_as() as api:
            activated = api.post(f"{BASE_URL}/{user_ids[0]}/activate")
            deactivated = api.post(f"{BASE_URL}/{user_ids[0]}/deactivate")

        assert activated.status_code == status.HTTP_200_OK, activated.text
        assert activated.json()["is_active"] is True
        assert {"password", "password_hash", "access_token", "token"}.isdisjoint(activated.json())
        assert deactivated.status_code == status.HTTP_200_OK, deactivated.text
        assert deactivated.json()["is_active"] is False

        with SessionLocal() as db:
            target = db.get(User, user_ids[0])
            assert target is not None
            assert target.id == immutable_fields["id"]
            assert target.email == immutable_fields["email"]
            assert target.password_hash == immutable_fields["password_hash"]
            assert target.role == immutable_fields["role"]
            assert target.record_number == immutable_fields["record_number"]


def test_admin_activation_and_deactivation_are_idempotent():
    """I accept repeated activation-state requests as successful no-ops."""

    with temporary_users({"is_active": False}) as user_ids, authenticated_as() as api:
        first_activation = api.post(f"{BASE_URL}/{user_ids[0]}/activate")
        repeated_activation = api.post(f"{BASE_URL}/{user_ids[0]}/activate")
        first_deactivation = api.post(f"{BASE_URL}/{user_ids[0]}/deactivate")
        repeated_deactivation = api.post(f"{BASE_URL}/{user_ids[0]}/deactivate")

    assert first_activation.status_code == status.HTTP_200_OK
    assert repeated_activation.status_code == status.HTTP_200_OK
    assert first_activation.json()["is_active"] is True
    assert repeated_activation.json()["is_active"] is True
    assert first_deactivation.status_code == status.HTTP_200_OK
    assert repeated_deactivation.status_code == status.HTTP_200_OK
    assert first_deactivation.json()["is_active"] is False
    assert repeated_deactivation.json()["is_active"] is False


def test_admin_can_self_deactivate_when_another_active_admin_remains():
    """I permit self-deactivation when it leaves another active administrator."""

    with temporary_users({"role": ADMIN}, {"role": ADMIN}) as user_ids:
        with SessionLocal() as db:
            actor = db.get(User, user_ids[0])
            assert actor is not None
        app.dependency_overrides[get_current_user] = lambda: actor
        try:
            response = client.post(f"{BASE_URL}/{user_ids[0]}/deactivate")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == status.HTTP_200_OK, response.text
    assert response.json()["is_active"] is False


def test_admin_cannot_deactivate_the_last_active_admin():
    """I preserve the final active administrator, including self-deactivation."""

    with temporary_users({"role": ADMIN}) as user_ids:
        with SessionLocal() as db:
            actor = db.get(User, user_ids[0])
            assert actor is not None
        app.dependency_overrides[get_current_user] = lambda: actor
        try:
            response = client.post(f"{BASE_URL}/{user_ids[0]}/deactivate")
        finally:
            app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "The last active administrator cannot be deactivated."


def test_concurrent_cross_deactivations_leave_one_admin_and_reject_waiting_actor():
    """I serialize cross-deactivation so a waiting deactivated actor loses access."""

    with temporary_users({"role": ADMIN}, {"role": ADMIN}) as user_ids:
        start = Barrier(2)
        responses: list[int] = []

        def deactivate_other(actor_id: UUID, target_id: UUID) -> None:
            headers = {"Authorization": f"Bearer {create_access_token(actor_id)}"}
            with TestClient(app) as concurrent_client:
                start.wait()
                response = concurrent_client.post(
                    f"{BASE_URL}/{target_id}/deactivate",
                    headers=headers,
                )
                responses.append(response.status_code)

        threads = [
            Thread(target=deactivate_other, args=(user_ids[0], user_ids[1])),
            Thread(target=deactivate_other, args=(user_ids[1], user_ids[0])),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        assert all(not thread.is_alive() for thread in threads)

        with SessionLocal() as db:
            active_admin_count = db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.role == ADMIN, User.is_active.is_(True))
            )

    assert sorted(responses) == [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN]
    assert active_admin_count == 1


def test_deactivation_revokes_existing_token_access_immediately():
    """I recheck database activation state for requests made with an old token."""

    with temporary_users({"role": BUSINESS_ANALYST}) as user_ids:
        headers = {"Authorization": f"Bearer {create_access_token(user_ids[0])}"}
        with authenticated_as() as api:
            deactivation = api.post(f"{BASE_URL}/{user_ids[0]}/deactivate")
        profile = client.get("/api/v1/auth/me", headers=headers)

    assert deactivation.status_code == status.HTTP_200_OK, deactivation.text
    assert profile.status_code == status.HTTP_403_FORBIDDEN
    assert profile.json()["detail"] == "User account is inactive."


def test_admin_user_endpoints_require_administrator_role():
    """I deny authenticated analysts and reviewers access to both endpoints."""

    for role in (BUSINESS_ANALYST, REVIEWER):
        with authenticated_as(role) as api:
            list_response = api.get(BASE_URL)
            detail_response = api.get(f"{BASE_URL}/{uuid4()}")
            create_response = api.post(
                BASE_URL,
                json={
                    "email": f"unauthorized-{uuid4().hex}@example.com",
                    "full_name": "Unauthorized User",
                    "password": "TestPassword123!",
                },
            )
            update_response = api.patch(
                f"{BASE_URL}/{uuid4()}", json={"full_name": "Unauthorized User"}
            )
            activate_response = api.post(f"{BASE_URL}/{uuid4()}/activate")
            deactivate_response = api.post(f"{BASE_URL}/{uuid4()}/deactivate")

        assert list_response.status_code == status.HTTP_403_FORBIDDEN
        assert detail_response.status_code == status.HTTP_403_FORBIDDEN
        assert create_response.status_code == status.HTTP_403_FORBIDDEN
        assert update_response.status_code == status.HTTP_403_FORBIDDEN
        assert activate_response.status_code == status.HTTP_403_FORBIDDEN
        assert deactivate_response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("url", [BASE_URL, f"{BASE_URL}/{uuid4()}"])
def test_admin_user_endpoints_reject_missing_and_invalid_tokens(url):
    """I preserve the existing authentication failures for both endpoints."""

    missing_response = client.get(url)
    invalid_response = client.get(
        url,
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert missing_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert invalid_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_admin_user_create_rejects_missing_and_invalid_tokens():
    """I require valid authentication before processing create payloads."""

    payload = {
        "email": f"missing-token-{uuid4().hex}@example.com",
        "full_name": "Missing Token User",
        "password": "TestPassword123!",
    }
    missing_response = client.post(BASE_URL, json=payload)
    invalid_response = client.post(
        BASE_URL,
        json=payload,
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert missing_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert invalid_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_inactive_administrator_cannot_access_admin_user_endpoints():
    """I reject an inactive administrator even with a valid signed token."""

    with temporary_users({"role": ADMIN, "is_active": False}) as user_ids:
        headers = {"Authorization": f"Bearer {create_access_token(user_ids[0])}"}
        list_response = client.get(BASE_URL, headers=headers)
        detail_response = client.get(f"{BASE_URL}/{user_ids[0]}", headers=headers)

    assert list_response.status_code == status.HTTP_403_FORBIDDEN
    assert detail_response.status_code == status.HTTP_403_FORBIDDEN
