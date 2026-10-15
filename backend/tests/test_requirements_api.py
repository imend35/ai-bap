
"""I test requirement management with JWT authentication and RBAC."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Project, Requirement
from app.role_permissions import ADMIN, BUSINESS_ANALYST, REVIEWER
from app.security import get_current_user


client = TestClient(app)
BASE_URL = "/api/v1/requirements"


@pytest.fixture
def authenticated_user():
    """I provide a configurable authenticated user for API tests."""

    user = SimpleNamespace(
        id=uuid4(),
        role=BUSINESS_ANALYST,
        is_active=True,
    )

    # I override authentication without exposing real credentials.
    app.dependency_overrides[get_current_user] = lambda: user

    yield user

    # I restore the original authentication dependency after each test.
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def test_project():
    """I create and clean up a temporary PostgreSQL project."""

    with SessionLocal() as db:
        project = Project(
            name="AI BAP Requirements JWT Test",
            description="Temporary project for requirement API tests",
            status="planned",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id = project.id

    yield project_id

    # I remove the temporary project and its requirements.
    with SessionLocal() as db:
        project = db.get(Project, project_id)

        if project is not None:
            db.delete(project)
            db.commit()


@pytest.fixture
def test_requirement(test_project):
    """I create a temporary requirement for detail and update tests."""

    with SessionLocal() as db:
        requirement = Requirement(
            project_id=test_project,
            title="User Authentication",
            description="Users must sign in securely.",
            priority="medium",
            status="draft",
        )
        db.add(requirement)
        db.commit()
        db.refresh(requirement)
        requirement_id = requirement.id

    return requirement_id


def requirement_payload(project_id):
    """I build a valid requirement creation payload."""

    return {
        "project_id": str(project_id),
        "title": "User Authentication",
        "description": "Users must sign in securely.",
        "priority": "high",
        "status": "draft",
    }


def test_list_requirements_for_existing_project(
    authenticated_user,
    test_project,
):
    """I verify that an existing project returns its requirements."""

    response = client.get(
        BASE_URL,
        params={"project_id": str(test_project)},
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 20
    assert data["offset"] == 0


def test_list_requirements_for_nonexistent_project(authenticated_user):
    """I verify that an unknown project returns HTTP 404."""

    response = client.get(
        BASE_URL,
        params={"project_id": str(uuid4())},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project not found."


def test_list_requirements_without_project_id(authenticated_user):
    """I verify that project_id is a required query parameter."""

    response = client.get(BASE_URL)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_requirements_with_invalid_project_id(authenticated_user):
    """I verify that invalid project identifiers are rejected."""

    response = client.get(
        BASE_URL,
        params={"project_id": "invalid-uuid"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_requirements_without_token():
    """I reject unauthenticated requirement listing requests."""

    response = client.get(
        BASE_URL,
        params={"project_id": str(uuid4())},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Missing bearer token."


def test_list_requirements_with_invalid_token():
    """I reject invalid JWT credentials."""

    response = client.get(
        BASE_URL,
        params={"project_id": str(uuid4())},
        headers={"Authorization": "Bearer invalid-jwt-token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid or expired access token."


def test_list_requirements_with_invalid_limit(authenticated_user):
    """I reject pagination limits outside the allowed range."""

    response = client.get(
        BASE_URL,
        params={
            "project_id": str(uuid4()),
            "limit": 0,
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_requirements_filters_by_project_and_paginates(
    authenticated_user,
):
    """I verify project filtering, pagination, and total counts."""

    with SessionLocal() as db:
        first_project = Project(
            name="AI BAP Requirements Project A",
            status="planned",
        )
        second_project = Project(
            name="AI BAP Requirements Project B",
            status="planned",
        )

        db.add_all([first_project, second_project])
        db.flush()

        first_project_id = first_project.id
        second_project_id = second_project.id

        requirements = [
            Requirement(
                project_id=first_project_id,
                title="Authentication Requirement",
                description="Users must sign in securely.",
                priority="high",
                status="draft",
            ),
            Requirement(
                project_id=first_project_id,
                title="Reporting Requirement",
                description="Users must generate reports.",
                priority="medium",
                status="draft",
            ),
            Requirement(
                project_id=second_project_id,
                title="Notification Requirement",
                description="Users must receive notifications.",
                priority="low",
                status="draft",
            ),
        ]

        db.add_all(requirements)
        db.commit()

    try:
        first_response = client.get(
            BASE_URL,
            params={
                "project_id": str(first_project_id),
                "limit": 1,
                "offset": 0,
            },
        )

        assert first_response.status_code == status.HTTP_200_OK

        first_page = first_response.json()

        assert first_page["total"] == 2
        assert first_page["limit"] == 1
        assert first_page["offset"] == 0
        assert len(first_page["items"]) == 1
        assert first_page["items"][0]["project_id"] == str(first_project_id)

        second_response = client.get(
            BASE_URL,
            params={
                "project_id": str(first_project_id),
                "limit": 1,
                "offset": 1,
            },
        )

        assert second_response.status_code == status.HTTP_200_OK

        second_page = second_response.json()

        assert second_page["total"] == 2
        assert second_page["offset"] == 1
        assert len(second_page["items"]) == 1
        assert second_page["items"][0]["project_id"] == str(first_project_id)

        assert (
            first_page["items"][0]["id"]
            != second_page["items"][0]["id"]
        )

        other_response = client.get(
            BASE_URL,
            params={"project_id": str(second_project_id)},
        )

        assert other_response.status_code == status.HTTP_200_OK

        other_page = other_response.json()

        assert other_page["total"] == 1
        assert len(other_page["items"]) == 1
        assert other_page["items"][0]["project_id"] == str(second_project_id)

    finally:
        # I clean up both projects and their associated requirements.
        with SessionLocal() as db:
            for project_id in (first_project_id, second_project_id):
                project = db.get(Project, project_id)

                if project is not None:
                    db.delete(project)

            db.commit()


def test_create_requirement_successfully(
    authenticated_user,
    test_project,
):
    """I verify requirement creation and PostgreSQL persistence."""

    response = client.post(
        BASE_URL,
        json=requirement_payload(test_project),
    )

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    assert data["project_id"] == str(test_project)
    assert data["title"] == "User Authentication"
    assert data["description"] == "Users must sign in securely."
    assert data["priority"] == "high"
    assert data["status"] == "draft"
    assert data["id"]
    assert data["created_at"]
    assert data["updated_at"]

    # I confirm that the requirement was saved in PostgreSQL.
    with SessionLocal() as db:
        requirement = db.get(Requirement, data["id"])

        assert requirement is not None
        assert requirement.project_id == test_project
        assert requirement.title == "User Authentication"


def test_create_requirement_with_default_values(
    authenticated_user,
    test_project,
):
    """I verify default priority and status values."""

    response = client.post(
        BASE_URL,
        json={
            "project_id": str(test_project),
            "title": "Generate User Stories",
            "description": "The system must generate user stories.",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["priority"] == "medium"
    assert response.json()["status"] == "draft"


def test_create_requirement_for_nonexistent_project(authenticated_user):
    """I reject creation when the parent project does not exist."""

    response = client.post(
        BASE_URL,
        json=requirement_payload(uuid4()),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project not found."


def test_create_requirement_without_project_id(authenticated_user):
    """I reject creation without a project identifier."""

    response = client.post(
        BASE_URL,
        json={
            "title": "User Authentication",
            "description": "Users must sign in securely.",
        },
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_requirement_with_invalid_priority(authenticated_user):
    """I reject unsupported requirement priorities."""

    payload = requirement_payload(uuid4())
    payload["priority"] = "urgent"

    response = client.post(BASE_URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_requirement_with_long_description(authenticated_user):
    """I reject descriptions longer than the allowed limit."""

    payload = requirement_payload(uuid4())
    payload["description"] = "A" * 5001

    response = client.post(BASE_URL, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_requirement_without_token():
    """I reject requirement creation without authentication."""

    response = client.post(
        BASE_URL,
        json=requirement_payload(uuid4()),
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_requirement_with_invalid_token():
    """I reject requirement creation with an invalid JWT."""

    response = client.post(
        BASE_URL,
        json=requirement_payload(uuid4()),
        headers={"Authorization": "Bearer invalid-jwt-token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_requirement_successfully(
    authenticated_user,
    test_project,
    test_requirement,
):
    """I retrieve an existing requirement by its identifier."""

    response = client.get(
        f"{BASE_URL}/{test_requirement}",
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == str(test_requirement)
    assert data["project_id"] == str(test_project)
    assert data["title"] == "User Authentication"
    assert data["description"] == "Users must sign in securely."
    assert data["priority"] == "medium"
    assert data["status"] == "draft"
    assert data["created_at"]
    assert data["updated_at"]


def test_get_nonexistent_requirement(authenticated_user):
    """I return HTTP 404 for an unknown requirement."""

    response = client.get(f"{BASE_URL}/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Requirement not found."


def test_get_requirement_with_invalid_uuid(authenticated_user):
    """I reject malformed requirement identifiers."""

    response = client.get(f"{BASE_URL}/invalid-uuid")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_requirement_without_token():
    """I reject unauthenticated requirement detail requests."""

    response = client.get(f"{BASE_URL}/{uuid4()}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_requirement_partially_and_persist_changes(
    authenticated_user,
    test_project,
    test_requirement,
):
    """I update selected fields and preserve unchanged values."""

    response = client.patch(
        f"{BASE_URL}/{test_requirement}",
        json={
            "priority": "critical",
            "status": "in_review",
        },
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == str(test_requirement)
    assert data["project_id"] == str(test_project)
    assert data["title"] == "User Authentication"
    assert data["description"] == "Users must sign in securely."
    assert data["priority"] == "critical"
    assert data["status"] == "in_review"

    # I verify that the updated fields were persisted in PostgreSQL.
    with SessionLocal() as db:
        saved_requirement = db.get(Requirement, test_requirement)

        assert saved_requirement is not None
        assert saved_requirement.project_id == test_project
        assert saved_requirement.title == "User Authentication"
        assert saved_requirement.description == "Users must sign in securely."
        assert saved_requirement.priority == "critical"
        assert saved_requirement.status == "in_review"


def test_update_nonexistent_requirement(authenticated_user):
    """I return HTTP 404 when updating an unknown requirement."""

    response = client.patch(
        f"{BASE_URL}/{uuid4()}",
        json={"priority": "high"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Requirement not found."


def test_update_requirement_with_invalid_uuid(authenticated_user):
    """I reject malformed identifiers in update requests."""

    response = client.patch(
        f"{BASE_URL}/invalid-uuid",
        json={"priority": "high"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_requirement_with_empty_payload(authenticated_user):
    """I reject empty requirement update payloads."""

    response = client.patch(
        f"{BASE_URL}/{uuid4()}",
        json={},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_requirement_with_invalid_priority(authenticated_user):
    """I reject invalid priority values in update requests."""

    response = client.patch(
        f"{BASE_URL}/{uuid4()}",
        json={"priority": "urgent"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_requirement_with_null_status(authenticated_user):
    """I reject null values for required status fields."""

    response = client.patch(
        f"{BASE_URL}/{uuid4()}",
        json={"status": None},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_requirement_without_token():
    """I reject unauthenticated requirement update requests."""

    response = client.patch(
        f"{BASE_URL}/{uuid4()}",
        json={"priority": "high"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize(
    "role",
    [ADMIN, BUSINESS_ANALYST, REVIEWER],
)
def test_authorized_roles_can_list_requirements(
    authenticated_user,
    test_project,
    role,
):
    """I allow all supported roles to list requirements."""

    authenticated_user.role = role

    response = client.get(
        BASE_URL,
        params={"project_id": str(test_project)},
    )

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "role",
    [ADMIN, BUSINESS_ANALYST, REVIEWER],
)
def test_authorized_roles_can_view_requirement(
    authenticated_user,
    test_requirement,
    role,
):
    """I allow all supported roles to view requirement details."""

    authenticated_user.role = role

    response = client.get(f"{BASE_URL}/{test_requirement}")

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize(
    "role",
    [ADMIN, BUSINESS_ANALYST],
)
def test_editing_roles_can_create_requirements(
    authenticated_user,
    test_project,
    role,
):
    """I allow administrators and analysts to create requirements."""

    authenticated_user.role = role

    response = client.post(
        BASE_URL,
        json=requirement_payload(test_project),
    )

    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.parametrize(
    "role",
    [ADMIN, BUSINESS_ANALYST],
)
def test_editing_roles_can_update_requirements(
    authenticated_user,
    test_requirement,
    role,
):
    """I allow administrators and analysts to update requirements."""

    authenticated_user.role = role

    response = client.patch(
        f"{BASE_URL}/{test_requirement}",
        json={"priority": "high"},
    )

    assert response.status_code == status.HTTP_200_OK


def test_reviewer_cannot_create_requirement(
    authenticated_user,
    test_project,
):
    """I prevent reviewers from creating requirements."""

    authenticated_user.role = REVIEWER

    response = client.post(
        BASE_URL,
        json=requirement_payload(test_project),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_reviewer_cannot_update_requirement(
    authenticated_user,
    test_requirement,
):
    """I prevent reviewers from updating requirements."""

    authenticated_user.role = REVIEWER

    response = client.patch(
        f"{BASE_URL}/{test_requirement}",
        json={"priority": "high"},
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
