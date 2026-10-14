
"""Test User Story API behavior."""

from fastapi import status
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import SessionLocal
from app.main import app
from app.models import Project, Requirement

client = TestClient(app)


def get_auth_headers() -> dict[str, str]:
    """Return valid authentication headers for API tests."""
    token = get_settings().demo_access_token.get_secret_value()
    return {"Authorization": f"Bearer {token}"}


def test_list_user_stories_for_existing_requirement():
    """Verify that an existing requirement returns an empty user story list."""
    with SessionLocal() as db:
        project = Project(
            name="AI BAP User Story Listing Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="User Authentication",
            description="Users must sign in securely.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.commit()

        project_id = project.id
        requirement_id = requirement.id

    try:
        response = client.get(
            "/api/v1/user-stories",
            params={"requirement_id": str(requirement_id)},
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["items"] == []
        assert data["total"] == 0
        assert data["limit"] == 20
        assert data["offset"] == 0

    finally:
        # Remove the temporary project and its related records.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()

def test_create_user_story_successfully():
    """Verify that a user story is created and persisted in PostgreSQL."""
    from app.models import UserStory

    with SessionLocal() as db:
        project = Project(
            name="AI BAP User Story Creation Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="User Authentication",
            description="Users must sign in securely.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.commit()

        project_id = project.id
        requirement_id = requirement.id

    try:
        response = client.post(
            "/api/v1/user-stories",
            json={
                "requirement_id": str(requirement_id),
                "title": "Login with Email",
                "description": (
                    "As a user, I want to log in with my email "
                    "so that I can access my account."
                ),
                "acceptance_criteria": [
                    "Given valid credentials, login succeeds.",
                    "Given invalid credentials, an error is displayed.",
                ],
                "status": "draft",
            },
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()

        assert data["requirement_id"] == str(requirement_id)
        assert data["title"] == "Login with Email"
        assert data["status"] == "draft"
        assert len(data["acceptance_criteria"]) == 2
        assert data["id"]
        assert data["created_at"]
        assert data["updated_at"]

        # Verify that the user story was persisted in PostgreSQL.
        with SessionLocal() as db:
            saved_story = db.get(UserStory, data["id"])

            assert saved_story is not None
            assert saved_story.requirement_id == requirement_id
            assert saved_story.title == "Login with Email"
            assert len(saved_story.acceptance_criteria) == 2

    finally:
        # Remove temporary test data and associated user stories.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()

def test_get_user_story_successfully():
    """Verify that an existing user story can be retrieved by ID."""
    from app.models import UserStory

    with SessionLocal() as db:
        project = Project(
            name="AI BAP User Story Detail Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="User Authentication",
            description="Users must sign in securely.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.flush()

        story = UserStory(
            requirement_id=requirement.id,
            title="Login with Email",
            description="As a user, I want to log in with my email.",
            acceptance_criteria=[
                "Given valid credentials, login succeeds.",
                "Given invalid credentials, an error is displayed.",
            ],
            status="draft",
        )
        db.add(story)
        db.commit()

        project_id = project.id
        requirement_id = requirement.id
        story_id = story.id

    try:
        response = client.get(
            f"/api/v1/user-stories/{story_id}",
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["id"] == str(story_id)
        assert data["requirement_id"] == str(requirement_id)
        assert data["title"] == "Login with Email"
        assert data["description"] == (
            "As a user, I want to log in with my email."
        )
        assert len(data["acceptance_criteria"]) == 2
        assert data["status"] == "draft"
        assert data["created_at"]
        assert data["updated_at"]

    finally:
        # Remove temporary test data and associated user stories.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()

def test_update_user_story_partially_and_persist_changes():
    """Verify partial updates preserve other fields and persist in PostgreSQL."""
    from app.models import UserStory

    with SessionLocal() as db:
        project = Project(
            name="AI BAP User Story Update Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="User Authentication",
            description="Users must sign in securely.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.flush()

        story = UserStory(
            requirement_id=requirement.id,
            title="Login with Email",
            description="As a user, I want to log in with my email.",
            acceptance_criteria=[
                "Given valid credentials, login succeeds.",
            ],
            status="draft",
        )
        db.add(story)
        db.commit()

        project_id = project.id
        requirement_id = requirement.id
        story_id = story.id

    try:
        response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={
                "status": "in_review",
                "acceptance_criteria": [
                    "Given valid credentials, login succeeds.",
                    "Given invalid credentials, an error is displayed.",
                ],
            },
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["id"] == str(story_id)
        assert data["requirement_id"] == str(requirement_id)
        assert data["title"] == "Login with Email"
        assert data["description"] == (
            "As a user, I want to log in with my email."
        )
        assert data["status"] == "in_review"
        assert len(data["acceptance_criteria"]) == 2

        # Verify that the updated values were persisted in PostgreSQL.
        with SessionLocal() as db:
            saved_story = db.get(UserStory, story_id)

            assert saved_story is not None
            assert saved_story.requirement_id == requirement_id
            assert saved_story.title == "Login with Email"
            assert saved_story.status == "in_review"
            assert len(saved_story.acceptance_criteria) == 2

    finally:
        # Remove temporary test data and associated user stories.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()

def test_list_user_stories_without_token():
    """Verify that listing user stories requires authentication."""
    from uuid import uuid4

    response = client.get(
        "/api/v1/user-stories",
        params={"requirement_id": str(uuid4())},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_user_story_without_token():
    """Verify that creating user stories requires authentication."""
    from uuid import uuid4

    response = client.post(
        "/api/v1/user-stories",
        json={
            "requirement_id": str(uuid4()),
            "title": "Login with Email",
            "description": "Users can log in with their email.",
            "acceptance_criteria": [
                "Given valid credentials, login succeeds.",
            ],
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_user_story_without_token():
    """Verify that retrieving user stories requires authentication."""
    from uuid import uuid4

    response = client.get(
        f"/api/v1/user-stories/{uuid4()}",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_user_story_without_token():
    """Verify that updating user stories requires authentication."""
    from uuid import uuid4

    response = client.patch(
        f"/api/v1/user-stories/{uuid4()}",
        json={"status": "in_review"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_user_stories_with_invalid_token():
    """Verify that invalid authentication credentials are rejected."""
    from uuid import uuid4

    response = client.get(
        "/api/v1/user-stories",
        params={"requirement_id": str(uuid4())},
        headers={"Authorization": "Bearer invalid-demo-token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_list_user_stories_for_nonexistent_requirement():
    """Verify that an unknown requirement returns HTTP 404."""
    from uuid import uuid4

    response = client.get(
        "/api/v1/user-stories",
        params={"requirement_id": str(uuid4())},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Requirement not found."


def test_create_user_story_for_nonexistent_requirement():
    """Verify that a user story cannot reference an unknown requirement."""
    from uuid import uuid4

    response = client.post(
        "/api/v1/user-stories",
        json={
            "requirement_id": str(uuid4()),
            "title": "Login with Email",
            "description": "Users can log in with their email.",
            "acceptance_criteria": [
                "Given valid credentials, login succeeds.",
            ],
        },
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Requirement not found."


def test_get_nonexistent_user_story():
    """Verify that an unknown user story returns HTTP 404."""
    from uuid import uuid4

    response = client.get(
        f"/api/v1/user-stories/{uuid4()}",
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User Story not found."


def test_update_nonexistent_user_story():
    """Verify that updating an unknown user story returns HTTP 404."""
    from uuid import uuid4

    response = client.patch(
        f"/api/v1/user-stories/{uuid4()}",
        json={"status": "in_review"},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User Story not found."

def test_list_user_stories_without_requirement_id():
    """Verify that requirement_id is required for listing."""
    response = client.get(
        "/api/v1/user-stories",
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_user_stories_with_invalid_requirement_id():
    """Verify that invalid requirement UUID values are rejected."""
    response = client.get(
        "/api/v1/user-stories",
        params={"requirement_id": "invalid-uuid"},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_user_stories_with_invalid_limit():
    """Verify that pagination limits must be valid."""
    from uuid import uuid4

    response = client.get(
        "/api/v1/user-stories",
        params={
            "requirement_id": str(uuid4()),
            "limit": 0,
        },
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_user_story_without_requirement_id():
    """Verify that requirement_id is required during creation."""
    response = client.post(
        "/api/v1/user-stories",
        json={
            "title": "Login with Email",
            "description": "Users can log in with their email.",
            "acceptance_criteria": [
                "Given valid credentials, login succeeds.",
            ],
        },
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_user_story_with_invalid_status():
    """Verify that unsupported user story statuses are rejected."""
    from uuid import uuid4

    response = client.post(
        "/api/v1/user-stories",
        json={
            "requirement_id": str(uuid4()),
            "title": "Login with Email",
            "description": "Users can log in with their email.",
            "acceptance_criteria": [
                "Given valid credentials, login succeeds.",
            ],
            "status": "completed",
        },
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_user_story_with_blank_acceptance_criterion():
    """Verify that blank acceptance criteria are rejected."""
    from uuid import uuid4

    response = client.post(
        "/api/v1/user-stories",
        json={
            "requirement_id": str(uuid4()),
            "title": "Login with Email",
            "description": "Users can log in with their email.",
            "acceptance_criteria": ["   "],
        },
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_user_story_with_too_many_acceptance_criteria():
    """Verify that more than 30 acceptance criteria are rejected."""
    from uuid import uuid4

    response = client.post(
        "/api/v1/user-stories",
        json={
            "requirement_id": str(uuid4()),
            "title": "Login with Email",
            "description": "Users can log in with their email.",
            "acceptance_criteria": ["Valid criterion"] * 31,
        },
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_user_story_with_invalid_uuid():
    """Verify that invalid user story UUID values are rejected."""
    response = client.get(
        "/api/v1/user-stories/invalid-uuid",
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_user_story_with_empty_payload():
    """Verify that empty PATCH requests are rejected."""
    from uuid import uuid4

    response = client.patch(
        f"/api/v1/user-stories/{uuid4()}",
        json={},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_user_story_with_null_status():
    """Verify that null cannot replace the user story status."""
    from uuid import uuid4

    response = client.patch(
        f"/api/v1/user-stories/{uuid4()}",
        json={"status": None},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_user_story_with_invalid_uuid():
    """Verify that invalid UUID values are rejected during updates."""
    response = client.patch(
        "/api/v1/user-stories/invalid-uuid",
        json={"status": "in_review"},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
