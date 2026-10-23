"""I verify environment bootstrap behavior against the guarded isolated database."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from app.database import SessionLocal
from app.initial_admin_bootstrap import (
    INITIAL_ADMIN_BOOTSTRAP_ENABLED,
    INITIAL_ADMIN_EMAIL,
    INITIAL_ADMIN_FULL_NAME,
    INITIAL_ADMIN_PASSWORD,
    EnvironmentBootstrapResult,
    bootstrap_initial_admin_from_environment,
)
from app.main import app
from app.models.user import User
from app.password_service import hash_password, verify_password
from app.role_permissions import ADMIN, BUSINESS_ANALYST


def bootstrap_environment(email: str) -> dict[str, str]:
    """Create a unique, test-only bootstrap configuration."""
    return {
        INITIAL_ADMIN_BOOTSTRAP_ENABLED: "true",
        INITIAL_ADMIN_EMAIL: email,
        INITIAL_ADMIN_FULL_NAME: "Isolated Bootstrap Administrator",
        INITIAL_ADMIN_PASSWORD: "IsolatedBootstrapPassword123!",
    }


def active_admin_count() -> int:
    """Count active administrators without returning their details."""
    with SessionLocal() as db:
        return (
            db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.role == ADMIN, User.is_active.is_(True))
            )
            or 0
        )


def delete_test_users(*emails: str) -> None:
    """Remove only unique users created by this isolated test module."""
    with SessionLocal() as db:
        db.execute(delete(User).where(User.email.in_(emails)))
        db.commit()


def bootstrap_with_safe_diagnostics(
    environment: dict[str, str],
) -> tuple[EnvironmentBootstrapResult, list[str]]:
    """Return only test-safe database-failure classifications for assertions."""
    diagnostics: list[str] = []
    result = bootstrap_initial_admin_from_environment(
        environment,
        diagnostic_reporter=diagnostics.append,
    )
    return result, diagnostics


def test_environment_bootstrap_creates_one_admin_repeats_safely_and_can_log_in() -> None:
    """I create at most one admin and prove the resulting account can authenticate."""
    email = f"bootstrap-login-{uuid4().hex}@example.com"
    different_email = f"bootstrap-repeat-{uuid4().hex}@example.com"
    assert active_admin_count() == 0

    try:
        creation_result, creation_diagnostics = bootstrap_with_safe_diagnostics(
            bootstrap_environment(email)
        )
        assert creation_result is EnvironmentBootstrapResult.CREATED, creation_diagnostics
        repeat_result, repeat_diagnostics = bootstrap_with_safe_diagnostics(
            bootstrap_environment(different_email)
        )
        assert repeat_result is EnvironmentBootstrapResult.ACTIVE_ADMIN_EXISTS, repeat_diagnostics
        assert active_admin_count() == 1

        with TestClient(app) as client:
            response = client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": "IsolatedBootstrapPassword123!"},
            )

        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"
    finally:
        delete_test_users(email, different_email)


def test_environment_bootstrap_is_concurrent_safe_and_does_not_overwrite_users() -> None:
    """I retain existing users and allow only one concurrent first administrator."""
    existing_email = f"bootstrap-existing-{uuid4().hex}@example.com"
    first_email = f"bootstrap-first-{uuid4().hex}@example.com"
    second_email = f"bootstrap-second-{uuid4().hex}@example.com"
    original_name = "Existing Analyst"
    original_hash = hash_password("ExistingAnalystPassword123!")
    assert active_admin_count() == 0

    try:
        with SessionLocal() as db:
            db.add(
                User(
                    email=existing_email,
                    full_name=original_name,
                    password_hash=original_hash,
                    role=BUSINESS_ANALYST,
                    is_active=True,
                )
            )
            db.commit()

        conflict_result, conflict_diagnostics = bootstrap_with_safe_diagnostics(
            bootstrap_environment(existing_email)
        )
        assert conflict_result is EnvironmentBootstrapResult.EMAIL_EXISTS, conflict_diagnostics

        with SessionLocal() as db:
            existing_user = db.scalar(select(User).where(User.email == existing_email))
            assert existing_user is not None
            assert existing_user.full_name == original_name
            assert existing_user.role == BUSINESS_ANALYST
            assert verify_password("ExistingAnalystPassword123!", existing_user.password_hash)

        with ThreadPoolExecutor(max_workers=2) as executor:
            results = list(
                executor.map(
                    bootstrap_initial_admin_from_environment,
                    (bootstrap_environment(first_email), bootstrap_environment(second_email)),
                )
            )

        assert results.count(EnvironmentBootstrapResult.CREATED) == 1
        assert results.count(EnvironmentBootstrapResult.ACTIVE_ADMIN_EXISTS) == 1
        assert active_admin_count() == 1
    finally:
        delete_test_users(existing_email, first_email, second_email)
