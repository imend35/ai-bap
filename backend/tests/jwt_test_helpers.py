
"""I provide reusable JWT authentication helpers for API tests."""

from uuid import uuid4

from sqlalchemy.orm import Session

from app.jwt_service import create_access_token
from app.models.user import User


def create_test_user(
    db: Session,
    role: str,
) -> User:
    """I create a temporary active user with the requested role."""

    # I generate a unique email address to avoid test conflicts.
    email = f"jwt-test-{uuid4().hex}@example.com"

    # I create a user without exposing any real credentials.
    user = User(
        email=email,
        full_name=f"JWT Test {role.replace('_', ' ').title()}",
        password_hash="test-only-not-for-login",
        role=role,
        is_active=True,
    )

    db.add(user)
    db.flush()

    return user


def get_jwt_auth_headers(user: User) -> dict[str, str]:
    """I create valid JWT authentication headers for my test user."""

    # I sign an access token using the user's database identifier.
    token = create_access_token(user.id)

    return {
        "Authorization": f"Bearer {token}",
    }
