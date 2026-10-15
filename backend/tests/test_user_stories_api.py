
"""I test User Story API behavior, validation, and role-based access."""

from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Project, Requirement, UserStory
from app.role_permissions import ADMIN, BUSINESS_ANALYST, REVIEWER
from app.security import get_current_user


STORIES_URL = "/api/v1/user-stories"
READ_ROLES = [ADMIN, BUSINESS_ANALYST, REVIEWER]
WRITE_ROLES = [ADMIN, BUSINESS_ANALYST]


class MockUser:
    """I represent an authenticated user with a selected role."""

    def __init__(self, role: str):
        self.id = uuid4()
        self.role = role
        self.is_active = True


@pytest.fixture
def client():
    """I create an isolated API test client."""

    # I remove authentication overrides left by other tests.
    app.dependency_overrides.pop(get_current_user, None)

    with TestClient(app) as test_client:
        yield test_client

    # I restore the original authentication behavior.
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def authenticate():
    """I simulate an authenticated user with the requested role."""

    def set_role(role: str):
        user = MockUser(role)

        # I override the JWT current-user dependency for this test.
        app.dependency_overrides[get_current_user] = lambda: user

        return {"Authorization": "Bearer test-jwt-token"}

    yield set_role

    # I prevent mocked authentication from leaking into other tests.
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def story_factory():
    """I create temporary PostgreSQL records for my API tests."""

    project_ids = []

    def create_story(story_status=None):
        with SessionLocal() as db:
            project = Project(
                name=f"AI BAP User Story Test {uuid4()}",
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

            story_id = None

            if story_status is not None:
                story = UserStory(
                    requirement_id=requirement.id,
                    title="Login with Email",
                    description="As a user, I want to log in with my email.",
                    acceptance_criteria=[
                        "Given valid credentials, login succeeds."
                    ],
                    status=story_status,
                )
                db.add(story)
                db.flush()
                story_id = story.id

            db.commit()

            project_id = project.id
            requirement_id = requirement.id
            project_ids.append(project_id)

        return requirement_id, story_id

    yield create_story

    # I delete all temporary projects and their related records.
    with SessionLocal() as db:
        for project_id in project_ids:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)

        db.commit()


def story_payload(requirement_id, story_status="draft"):
    """I prepare a valid User Story creation request."""

    return {
        "requirement_id": str(requirement_id),
        "title": "Login with Email",
        "description": "Users can log in with their email.",
        "acceptance_criteria": [
            "Given valid credentials, login succeeds.",
            "Given invalid credentials, an error is displayed.",
        ],
        "status": story_status,
    }


@pytest.mark.parametrize("role", READ_ROLES)
def test_list_user_stories_for_existing_requirement(
    client, authenticate, story_factory, role
):
    """I verify that authorized roles can list user stories."""

    requirement_id, _ = story_factory()
    headers = authenticate(role)

    response = client.get(
        STORIES_URL,
        params={"requirement_id": str(requirement_id)},
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["items"] == []
    assert response.json()["total"] == 0
    assert response.json()["limit"] == 20
    assert response.json()["offset"] == 0


@pytest.mark.parametrize("role", WRITE_ROLES)
def test_create_user_story_successfully(
    client, authenticate, story_factory, role
):
    """I verify that authorized roles can create a draft."""

    requirement_id, _ = story_factory()
    headers = authenticate(role)

    response = client.post(
        STORIES_URL,
        json=story_payload(requirement_id),
        headers=headers,
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

    # I verify that the new story was persisted in PostgreSQL.
    with SessionLocal() as db:
        saved_story = db.get(UserStory, data["id"])

        assert saved_story is not None
        assert saved_story.requirement_id == requirement_id
        assert saved_story.status == "draft"


@pytest.mark.parametrize("role", READ_ROLES)
def test_get_user_story_successfully(
    client, authenticate, story_factory, role
):
    """I verify that authorized roles can retrieve a user story."""

    requirement_id, story_id = story_factory("draft")
    headers = authenticate(role)

    response = client.get(
        f"{STORIES_URL}/{story_id}",
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == str(story_id)
    assert data["requirement_id"] == str(requirement_id)
    assert data["title"] == "Login with Email"
    assert data["status"] == "draft"


@pytest.mark.parametrize("role", WRITE_ROLES)
def test_update_user_story_partially_and_persist_changes(
    client, authenticate, story_factory, role
):
    """I verify that authorized roles can submit stories for review."""

    _, story_id = story_factory("draft")
    headers = authenticate(role)

    response = client.patch(
        f"{STORIES_URL}/{story_id}",
        json={
            "status": "in_review",
            "acceptance_criteria": [
                "Given valid credentials, login succeeds.",
                "Given invalid credentials, an error is displayed.",
            ],
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "in_review"
    assert response.json()["title"] == "Login with Email"

    # I verify that the changes were saved in PostgreSQL.
    with SessionLocal() as db:
        saved_story = db.get(UserStory, story_id)

        assert saved_story is not None
        assert saved_story.status == "in_review"
        assert len(saved_story.acceptance_criteria) == 2


@pytest.mark.parametrize("method", ["get", "post", "patch"])
def test_user_story_endpoints_without_token(client, method):
    """I verify that protected endpoints reject missing credentials."""

    story_id = uuid4()

    if method == "get":
        response = client.get(
            STORIES_URL,
            params={"requirement_id": str(uuid4())},
        )
    elif method == "post":
        response = client.post(
            STORIES_URL,
            json=story_payload(uuid4()),
        )
    else:
        response = client.patch(
            f"{STORIES_URL}/{story_id}",
            json={"status": "in_review"},
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_user_story_without_token(client):
    """I verify that story details require authentication."""

    response = client.get(f"{STORIES_URL}/{uuid4()}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_user_stories_with_invalid_token(client):
    """I verify that an invalid JWT is rejected."""

    response = client.get(
        STORIES_URL,
        params={"requirement_id": str(uuid4())},
        headers={"Authorization": "Bearer invalid-jwt-token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("role", READ_ROLES)
def test_list_user_stories_for_nonexistent_requirement(
    client, authenticate, role
):
    """I verify that missing requirements return HTTP 404."""

    headers = authenticate(role)

    response = client.get(
        STORIES_URL,
        params={"requirement_id": str(uuid4())},
        headers=headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Requirement not found."


@pytest.mark.parametrize("role", WRITE_ROLES)
def test_create_user_story_for_nonexistent_requirement(
    client, authenticate, role
):
    """I reject stories referencing nonexistent requirements."""

    headers = authenticate(role)

    response = client.post(
        STORIES_URL,
        json=story_payload(uuid4()),
        headers=headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("role", READ_ROLES)
def test_get_nonexistent_user_story(client, authenticate, role):
    """I return HTTP 404 when the requested story does not exist."""

    headers = authenticate(role)

    response = client.get(
        f"{STORIES_URL}/{uuid4()}",
        headers=headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("role", WRITE_ROLES)
def test_update_nonexistent_user_story(client, authenticate, role):
    """I reject updates targeting nonexistent stories."""

    headers = authenticate(role)

    response = client.patch(
        f"{STORIES_URL}/{uuid4()}",
        json={"status": "in_review"},
        headers=headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize(
    "params",
    [
        {},
        {"requirement_id": "invalid-uuid"},
        {"requirement_id": str(uuid4()), "limit": 0},
    ],
)
def test_list_user_stories_with_invalid_parameters(
    client, authenticate, params
):
    """I validate required UUID and pagination parameters."""

    headers = authenticate(ADMIN)

    response = client.get(
        STORIES_URL,
        params=params,
        headers=headers,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    "payload",
    [
        {
            "title": "Login with Email",
            "description": "Users can log in.",
            "acceptance_criteria": ["Valid criterion"],
        },
        story_payload(uuid4(), "completed"),
        {
            **story_payload(uuid4()),
            "acceptance_criteria": ["   "],
        },
        {
            **story_payload(uuid4()),
            "acceptance_criteria": ["Valid criterion"] * 31,
        },
    ],
)
def test_create_user_story_with_invalid_payload(
    client, authenticate, payload
):
    """I reject invalid User Story creation requests."""

    headers = authenticate(ADMIN)

    response = client.post(
        STORIES_URL,
        json=payload,
        headers=headers,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"status": None},
    ],
)
def test_update_user_story_with_invalid_payload(
    client, authenticate, payload
):
    """I reject empty or invalid update requests."""

    headers = authenticate(ADMIN)

    response = client.patch(
        f"{STORIES_URL}/{uuid4()}",
        json=payload,
        headers=headers,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize("method", ["get", "patch"])
def test_user_story_with_invalid_uuid(client, authenticate, method):
    """I reject malformed User Story identifiers."""

    headers = authenticate(ADMIN)
    url = f"{STORIES_URL}/invalid-uuid"

    if method == "get":
        response = client.get(url, headers=headers)
    else:
        response = client.patch(
            url,
            json={"status": "in_review"},
            headers=headers,
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    "method",
    ["post", "patch", "generate"],
)
def test_reviewer_cannot_modify_user_stories(
    client, authenticate, method
):
    """I prevent reviewers from performing analyst operations."""

    headers = authenticate(REVIEWER)
    requirement_id = uuid4()

    if method == "post":
        response = client.post(
            STORIES_URL,
            json=story_payload(requirement_id),
            headers=headers,
        )
    elif method == "generate":
        response = client.post(
            f"{STORIES_URL}/generate",
            json={"requirement_id": str(requirement_id)},
            headers=headers,
        )
    else:
        response = client.patch(
            f"{STORIES_URL}/{uuid4()}",
            json={"status": "in_review"},
            headers=headers,
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.parametrize("role", WRITE_ROLES)
def test_create_user_story_must_start_in_draft(
    client, authenticate, story_factory, role
):
    """I prevent new stories from bypassing human review."""

    requirement_id, _ = story_factory()
    headers = authenticate(role)

    response = client.post(
        STORIES_URL,
        json=story_payload(requirement_id, "approved"),
        headers=headers,
    )

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.parametrize("role", WRITE_ROLES)
def test_approved_user_story_cannot_be_modified(
    client, authenticate, story_factory, role
):
    """I protect approved user stories against modifications."""

    _, story_id = story_factory("approved")
    headers = authenticate(role)

    response = client.patch(
        f"{STORIES_URL}/{story_id}",
        json={"title": "Modified Title"},
        headers=headers,
    )

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.parametrize("role", WRITE_ROLES)
@pytest.mark.parametrize("decision", ["approved", "rejected"])
def test_patch_cannot_make_approval_decisions(
    client, authenticate, story_factory, role, decision
):
    """I require approval decisions to use audited endpoints."""

    _, story_id = story_factory("in_review")
    headers = authenticate(role)

    response = client.patch(
        f"{STORIES_URL}/{story_id}",
        json={"status": decision},
        headers=headers,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN

    # I verify that a rejected PATCH did not modify the database.
    with SessionLocal() as db:
        saved_story = db.get(UserStory, story_id)

        assert saved_story.status == "in_review"


@pytest.mark.parametrize("role", WRITE_ROLES)
def test_invalid_status_transition_is_rejected(
    client, authenticate, story_factory, role
):
    """I reject invalid User Story workflow transitions."""

    _, story_id = story_factory("draft")
    headers = authenticate(role)

    response = client.patch(
        f"{STORIES_URL}/{story_id}",
        json={"status": "approved"},
        headers=headers,
    )

    assert response.status_code == status.HTTP_409_CONFLICT


@pytest.mark.parametrize("role", WRITE_ROLES)
def test_rejected_story_can_return_to_draft(
    client, authenticate, story_factory, role
):
    """I allow rejected stories to return to draft for revision."""

    _, story_id = story_factory("rejected")
    headers = authenticate(role)

    response = client.patch(
        f"{STORIES_URL}/{story_id}",
        json={"status": "draft"},
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "draft"
