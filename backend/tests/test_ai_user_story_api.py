
"""Test AI-assisted User Story generation API behavior."""

from unittest.mock import patch
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import SessionLocal
from app.main import app
from app.models import Project, Requirement
from app.services.ai.user_story_generator import (
    AIGenerationError,
    GeneratedUserStory,
)

client = TestClient(app)


def get_auth_headers() -> dict[str, str]:
    """Return valid authentication headers for API tests."""
    token = get_settings().demo_access_token.get_secret_value()
    return {"Authorization": f"Bearer {token}"}


def test_generate_user_story_for_missing_requirement() -> None:
    """Verify that a missing requirement returns HTTP 404."""

    response = client.post(
        "/api/v1/user-stories/generate",
        json={"requirement_id": str(uuid4())},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Requirement not found."


def test_generate_user_story_returns_draft_without_saving() -> None:
    """Verify that AI output is returned as a draft without persistence."""

    with SessionLocal() as db:
        project = Project(
            name="AI BAP AI Generation API Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="User Login",
            description="Users must be able to log in securely.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.commit()

        project_id = project.id
        requirement_id = requirement.id

    generated_story = GeneratedUserStory(
        title="Secure User Login",
        description=(
            "As a user, I want to log in securely, "
            "so that I can access my account."
        ),
        acceptance_criteria=[
            "Given valid credentials, when I log in, then access is granted."
        ],
    )

    try:
        with patch(
            "app.routers.user_stories.generate_user_story",
            return_value=generated_story,
        ) as mocked_generator:
            response = client.post(
                "/api/v1/user-stories/generate",
                json={"requirement_id": str(requirement_id)},
                headers=get_auth_headers(),
            )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["requirement_id"] == str(requirement_id)
        assert data["title"] == "Secure User Login"
        assert len(data["acceptance_criteria"]) == 1
        assert data["requires_human_review"] is True
        assert data["saved_to_database"] is False

        mocked_generator.assert_called_once_with(
            requirement_title="User Login",
            requirement_description="Users must be able to log in securely.",
            requirement_priority="high",
        )

        # AI taslağının otomatik kaydedilmediğini doğruluyorum.
        with SessionLocal() as db:
            saved_stories = db.query(
                __import__("app.models", fromlist=["UserStory"]).UserStory
            ).filter_by(requirement_id=requirement_id).all()

            assert saved_stories == []

    finally:
        with SessionLocal() as db:
            project = db.get(Project, project_id)
            if project is not None:
                db.delete(project)
                db.commit()


def test_generate_user_story_handles_ai_service_failure() -> None:
    """Verify that AI service failures return HTTP 503."""

    with SessionLocal() as db:
        project = Project(
            name="AI BAP AI Generation Failure Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="User Login",
            description="Users must be able to log in securely.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.commit()

        project_id = project.id
        requirement_id = requirement.id

    try:
        with patch(
            "app.routers.user_stories.generate_user_story",
            side_effect=AIGenerationError("Simulated AI failure."),
        ):
            response = client.post(
                "/api/v1/user-stories/generate",
                json={"requirement_id": str(requirement_id)},
                headers=get_auth_headers(),
            )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert response.json()["detail"] == (
            "AI user story generation is currently unavailable."
        )

    finally:
        with SessionLocal() as db:
            project = db.get(Project, project_id)
            if project is not None:
                db.delete(project)
                db.commit()


def test_generate_user_story_requires_authentication() -> None:
    """Verify that the generation endpoint requires authentication."""

    response = client.post(
        "/api/v1/user-stories/generate",
        json={"requirement_id": str(uuid4())},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
