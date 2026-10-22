
"""I test JWT access token security for AI BAP."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt

from app.config import get_settings
from app.jwt_service import create_access_token, verify_access_token


def test_create_and_verify_access_token():
    """I verify that a valid access token returns its user ID."""
    user_id = uuid4()

    token = create_access_token(user_id)

    assert isinstance(token, str)
    assert verify_access_token(token) == user_id


def test_modified_access_token_is_rejected():
    """I verify that a modified token signature is rejected."""
    user_id = uuid4()

    token = create_access_token(user_id)
    header, payload, signature = token.split(".")
    modified_signature = (
        ("A" if signature[0] != "A" else "B") + signature[1:]
    )
    modified_token = f"{header}.{payload}.{modified_signature}"

    assert verify_access_token(modified_token) is None


def test_expired_access_token_is_rejected():
    """I verify that an expired access token is rejected."""
    settings = get_settings()
    user_id = uuid4()

    expired_payload = {
        "sub": str(user_id),
        "iat": datetime.now(UTC) - timedelta(hours=2),
        "exp": datetime.now(UTC) - timedelta(hours=1),
        "type": "access",
    }

    expired_token = jwt.encode(
        expired_payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    assert verify_access_token(expired_token) is None


def test_wrong_token_type_is_rejected():
    """I verify that tokens with an unexpected type are rejected."""
    settings = get_settings()
    user_id = uuid4()

    payload = {
        "sub": str(user_id),
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=30),
        "type": "refresh",
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    assert verify_access_token(token) is None


def test_invalid_user_id_is_rejected():
    """I verify that a token with an invalid user ID is rejected."""
    settings = get_settings()

    payload = {
        "sub": "invalid-user-id",
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=30),
        "type": "access",
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    assert verify_access_token(token) is None


def test_missing_required_claim_is_rejected():
    """I verify that tokens missing required claims are rejected."""
    settings = get_settings()

    payload = {
        "sub": str(uuid4()),
        "exp": datetime.now(UTC) + timedelta(minutes=30),
        "type": "access",
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )

    assert verify_access_token(token) is None
