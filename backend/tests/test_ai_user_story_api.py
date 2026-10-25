
"""I test AI-assisted User Story generation and role-based access."""

from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.database import SessionLocal, get_db
from app.main import app
from app.models import Project, Requirement, UserStory
from app.role_permissions import ADMIN, BUSINESS_ANALYST, REVIEWER
from app.security import get_current_user
from app.services.ai.user_story_generator import (
    AIGenerationError,
    GeneratedUserStory,
)

GENERATE_URL = "/api/v1/user-stories/generate"
WRITE_ROLES = [ADMIN, BUSINESS_ANALYST]


class MockUser:
    """I represent an authenticated user with a selected role."""

    def __init__(self, role: str, email: str = "test-user@example.test"):
        self.id = uuid4()
        self.role = role
        self.email = email
        self.is_active = True


@pytest.fixture
def client():
    """I create a test client with isolated authentication overrides."""

    # I remove authentication overrides left by previous tests.
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)

    with TestClient(app) as test_client:
        yield test_client

    # I restore the original authentication behavior after each test.
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def authenticate():
    """I simulate an authenticated user with the selected role."""

    def set_role(role: str, email: str = "test-user@example.test"):
        user = MockUser(role, email)

        # I override the current-user dependency for role-based testing.
        app.dependency_overrides[get_current_user] = lambda: user

        return {"Authorization": "Bearer test-jwt-token"}

    yield set_role

    # I prevent authentication overrides from affecting other tests.
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def requirement_factory():
    """I create temporary PostgreSQL requirements for AI generation tests."""

    project_ids = []

    def create_requirement():
        with SessionLocal() as db:
            project = Project(
                name=f"AI BAP AI Generation Test {uuid4()}",
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
            project_ids.append(project_id)

        return requirement_id

    yield create_requirement

    # I remove the temporary projects and their related records.
    with SessionLocal() as db:
        for project_id in project_ids:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)

        db.commit()


@pytest.mark.parametrize("role", WRITE_ROLES)
def test_generate_user_story_for_missing_requirement(
    client, authenticate, role
):
    """I verify that missing requirements return HTTP 404."""

    headers = authenticate(role)

    response = client.post(
        GENERATE_URL,
        json={"requirement_id": str(uuid4())},
        headers=headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Requirement not found."


@pytest.mark.parametrize(
    ("role", "email"),
    [
        (BUSINESS_ANALYST, "banlyst@example.com"),
        (BUSINESS_ANALYST, " ReViWeR@Example.com "),
        (REVIEWER, "reviwer@example.com"),
    ],
)
def test_public_demo_accounts_cannot_generate_user_stories(
    client, authenticate, role, email
):
    """I block exact demo identities before requirement access or AI use."""

    headers = authenticate(role, email)
    app.dependency_overrides[get_db] = lambda: None

    with patch(
        "app.routers.user_stories.generate_user_story"
    ) as mocked_generator, patch(
        "app.routers.user_stories.resolve_project_id_for_requirement"
    ) as mocked_requirement_lookup:
        response = client.post(
            GENERATE_URL,
            json={"requirement_id": str(uuid4())},
            headers=headers,
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    if role == REVIEWER:
        assert response.json()["detail"] == (
            "You do not have permission to perform this action."
        )
    else:
        assert response.json()["detail"] == (
            "Live AI generation is unavailable for public demo accounts."
        )
    mocked_generator.assert_not_called()
    mocked_requirement_lookup.assert_not_called()


@pytest.mark.parametrize(
    ("role", "email"),
    [
        (BUSINESS_ANALYST, "banlyst+other@example.com"),
        (ADMIN, "admin@example.test"),
    ],
)
def test_non_demo_authorized_users_can_generate_user_stories(
    client, authenticate, role, email
):
    """I preserve generation for authorized non-demo users."""

    requirement_id = uuid4()
    headers = authenticate(role, email)
    requirement = type(
        "RequirementStub",
        (),
        {
            "id": requirement_id,
            "title": "User Login",
            "description": "Users must be able to log in securely.",
            "priority": "high",
        },
    )()

    class DatabaseStub:
        def get(self, model, selected_id):
            assert selected_id == requirement_id
            return requirement

        def commit(self):
            return None

    app.dependency_overrides[get_db] = lambda: DatabaseStub()
    generated_story = GeneratedUserStory(
        title="Secure User Login",
        description="A reviewed draft.",
        acceptance_criteria=["Given valid credentials, access is granted."],
    )

    with patch(
        "app.routers.user_stories.generate_user_story",
        return_value=generated_story,
    ) as mocked_generator, patch(
        "app.routers.user_stories.resolve_project_id_for_requirement",
        return_value=uuid4(),
    ), patch("app.routers.user_stories.lock_writable_project"):
        response = client.post(
            GENERATE_URL,
            json={"requirement_id": str(requirement_id)},
            headers=headers,
        )

    assert response.status_code == status.HTTP_200_OK
    mocked_generator.assert_called_once()


@pytest.mark.parametrize("role", WRITE_ROLES)
def test_generate_user_story_returns_draft_without_saving(
    client, authenticate, requirement_factory, role
):
    """I verify that AI output requires review and is not persisted."""

    requirement_id = requirement_factory()
    headers = authenticate(role)

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

    with patch(
        "app.routers.user_stories.generate_user_story",
        return_value=generated_story,
    ) as mocked_generator:
        response = client.post(
            GENERATE_URL,
            json={"requirement_id": str(requirement_id)},
            headers=headers,
        )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["requirement_id"] == str(requirement_id)
    assert data["title"] == "Secure User Login"
    assert len(data["acceptance_criteria"]) == 1
    assert data["requires_human_review"] is True
    assert data["saved_to_database"] is False

    # I verify that the AI generator received the requirement details.
    mocked_generator.assert_called_once_with(
        requirement_title="User Login",
        requirement_description="Users must be able to log in securely.",
        requirement_priority="high",
    )

    # I verify that no User Story was automatically saved.
    with SessionLocal() as db:
        saved_count = db.scalar(
            select(func.count())
            .select_from(UserStory)
            .where(UserStory.requirement_id == requirement_id)
        )

        assert saved_count == 0


@pytest.mark.parametrize("role", WRITE_ROLES)
def test_generate_user_story_handles_ai_service_failure(
    client, authenticate, requirement_factory, role
):
    """I verify that AI service failures return a controlled HTTP 503."""

    requirement_id = requirement_factory()
    headers = authenticate(role)

    with patch(
        "app.routers.user_stories.generate_user_story",
        side_effect=AIGenerationError("Simulated AI failure."),
    ):
        response = client.post(
            GENERATE_URL,
            json={"requirement_id": str(requirement_id)},
            headers=headers,
        )

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json()["detail"] == (
        "AI user story generation is currently unavailable."
    )


def test_generate_user_story_requires_authentication(client):
    """I verify that AI generation rejects missing authentication."""

    response = client.post(
        GENERATE_URL,
        json={"requirement_id": str(uuid4())},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_generate_user_story_rejects_invalid_token(client):
    """I verify that invalid JWT credentials cannot access AI generation."""

    response = client.post(
        GENERATE_URL,
        json={"requirement_id": str(uuid4())},
        headers={"Authorization": "Bearer invalid-jwt-token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_reviewer_cannot_generate_user_story(client, authenticate):
    """I verify that reviewers cannot invoke AI generation."""

    headers = authenticate(REVIEWER)
    app.dependency_overrides[get_db] = lambda: None

    # I ensure that the AI generator is never called for a forbidden role.
    with patch(
        "app.routers.user_stories.generate_user_story"
    ) as mocked_generator:
        response = client.post(
            GENERATE_URL,
            json={"requirement_id": str(uuid4())},
            headers=headers,
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    mocked_generator.assert_not_called()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"requirement_id": "invalid-uuid"},
    ],
)
def test_generate_user_story_rejects_invalid_payload(
    client, authenticate, payload
):
    """I verify that invalid AI generation requests are rejected."""

    headers = authenticate(ADMIN)

    response = client.post(
        GENERATE_URL,
        json=payload,
        headers=headers,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
