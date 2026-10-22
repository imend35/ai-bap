
"""I test sprint management and JWT-based role permissions."""

from uuid import UUID, uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Project, Sprint
from app.role_permissions import ADMIN, BUSINESS_ANALYST, REVIEWER
from app.security import get_current_user

SPRINTS_URL = "/api/v1/sprints"

UNKNOWN_ID = UUID("00000000-0000-0000-0000-000000000000")

SPRINT_PAYLOAD = {
    "name": "Sprint 1 - Development",
    "start_date": "2026-10-20",
    "end_date": "2026-11-03",
}


class MockUser:
    """I represent an authenticated user in role-based API tests."""

    def __init__(self, role: str):
        self.id = uuid4()
        self.role = role
        self.is_active = True


@pytest.fixture
def client():
    """I create an isolated API client for each test."""

    # I remove stale authentication overrides before each test.
    app.dependency_overrides.pop(get_current_user, None)

    with TestClient(app) as test_client:
        yield test_client

    # I restore the authentication dependency after each test.
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def authenticate():
    """I simulate authenticated users with explicitly selected roles."""

    def set_role(role: str):
        user = MockUser(role)

        # I replace only the current-user dependency for this test.
        app.dependency_overrides[get_current_user] = lambda: user

        return {"Authorization": "Bearer test-jwt-token"}

    yield set_role

    # I prevent role overrides from leaking into other tests.
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def project_id():
    """I create a temporary project and clean up its sprint records."""

    with SessionLocal() as db:
        project = Project(
            name=f"AI BAP Sprint Test {uuid4()}",
            status="planned",
        )

        db.add(project)
        db.commit()
        project_id = project.id

    yield project_id

    # I remove the temporary sprint records before deleting the project.
    with SessionLocal() as db:
        sprints = (
            db.query(Sprint)
            .filter(Sprint.project_id == project_id)
            .all()
        )

        for sprint in sprints:
            db.delete(sprint)

        db.flush()

        project = db.get(Project, project_id)

        if project is not None:
            db.delete(project)

        db.commit()


@pytest.fixture
def sprint_id(project_id):
    """I create a temporary sprint for retrieval and update tests."""

    with SessionLocal() as db:
        sprint = Sprint(
            project_id=project_id,
            name="Sprint 1 - Foundation",
            start_date=__import__("datetime").date(2026, 10, 20),
            end_date=__import__("datetime").date(2026, 11, 3),
            status="planned",
        )

        db.add(sprint)
        db.commit()

        return sprint.id


def test_list_sprints_for_nonexistent_project(client, authenticate):
    """I verify that an unknown project returns HTTP 404."""

    headers = authenticate(ADMIN)

    response = client.get(
        SPRINTS_URL,
        params={"project_id": str(UNKNOWN_ID)},
        headers=headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project not found."


@pytest.mark.parametrize("role", [ADMIN, BUSINESS_ANALYST])
def test_create_sprint_successfully(
    client,
    authenticate,
    project_id,
    role,
):
    """I verify that authorized users can create sprints."""

    headers = authenticate(role)

    response = client.post(
        SPRINTS_URL,
        json={
            "project_id": str(project_id),
            **SPRINT_PAYLOAD,
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_201_CREATED

    sprint = response.json()

    assert sprint["project_id"] == str(project_id)
    assert sprint["name"] == SPRINT_PAYLOAD["name"]
    assert sprint["start_date"] == SPRINT_PAYLOAD["start_date"]
    assert sprint["end_date"] == SPRINT_PAYLOAD["end_date"]
    assert sprint["status"] == "planned"
    assert "id" in sprint


@pytest.mark.parametrize("role", [ADMIN, BUSINESS_ANALYST, REVIEWER])
def test_list_sprints_successfully(
    client,
    authenticate,
    project_id,
    sprint_id,
    role,
):
    """I verify that every permitted role can list project sprints."""

    headers = authenticate(role)

    response = client.get(
        SPRINTS_URL,
        params={
            "project_id": str(project_id),
            "limit": 20,
            "offset": 0,
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["total"] == 1
    assert data["limit"] == 20
    assert data["offset"] == 0
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(sprint_id)
    assert data["items"][0]["project_id"] == str(project_id)


@pytest.mark.parametrize("role", [ADMIN, BUSINESS_ANALYST])
def test_update_sprint_successfully(
    client,
    authenticate,
    sprint_id,
    role,
):
    """I verify that authorized users can update existing sprints."""

    headers = authenticate(role)

    response = client.patch(
        f"{SPRINTS_URL}/{sprint_id}",
        json={
            "name": "Sprint 1 - Development",
            "status": "active",
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK

    sprint = response.json()

    assert sprint["id"] == str(sprint_id)
    assert sprint["name"] == "Sprint 1 - Development"
    assert sprint["status"] == "active"
    assert sprint["start_date"] == "2026-10-20"
    assert sprint["end_date"] == "2026-11-03"


def test_reject_invalid_sprint_date_update(
    client,
    authenticate,
    sprint_id,
):
    """I reject invalid date ranges without modifying stored data."""

    headers = authenticate(ADMIN)

    response = client.patch(
        f"{SPRINTS_URL}/{sprint_id}",
        json={"end_date": "2026-10-19"},
        headers=headers,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == (
        "Sprint end_date must be on or after start_date."
    )

    # I verify that the rejected update left the sprint unchanged.
    get_response = client.get(
        f"{SPRINTS_URL}/{sprint_id}",
        headers=headers,
    )

    assert get_response.status_code == status.HTTP_200_OK

    sprint = get_response.json()

    assert sprint["start_date"] == "2026-10-20"
    assert sprint["end_date"] == "2026-11-03"
    assert sprint["status"] == "planned"


@pytest.mark.parametrize("role", [ADMIN, BUSINESS_ANALYST, REVIEWER])
def test_get_sprint_successfully(
    client,
    authenticate,
    sprint_id,
    role,
):
    """I verify that permitted roles can retrieve sprint details."""

    headers = authenticate(role)

    response = client.get(
        f"{SPRINTS_URL}/{sprint_id}",
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == str(sprint_id)


@pytest.mark.parametrize(
    "method,path,json_payload,query_params",
    [
        ("GET", SPRINTS_URL, None, {"project_id": str(UNKNOWN_ID)}),
        ("POST", SPRINTS_URL, SPRINT_PAYLOAD, None),
        ("GET", f"{SPRINTS_URL}/{UNKNOWN_ID}", None, None),
        ("PATCH", f"{SPRINTS_URL}/{UNKNOWN_ID}", {"name": "Updated"}, None),
    ],
)
def test_reject_unauthenticated_requests(
    client,
    method,
    path,
    json_payload,
    query_params,
):
    """I verify that all sprint endpoints require authentication."""

    response = client.request(
        method,
        path,
        json=json_payload,
        params=query_params,
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_reviewer_cannot_create_sprint(
    client,
    authenticate,
    project_id,
):
    """I prevent reviewers from creating sprints."""

    headers = authenticate(REVIEWER)

    response = client.post(
        SPRINTS_URL,
        json={
            "project_id": str(project_id),
            **SPRINT_PAYLOAD,
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_reviewer_cannot_update_sprint(
    client,
    authenticate,
    sprint_id,
):
    """I prevent reviewers from updating sprints."""

    headers = authenticate(REVIEWER)

    response = client.patch(
        f"{SPRINTS_URL}/{sprint_id}",
        json={"name": "Unauthorized Update"},
        headers=headers,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_create_sprint_for_nonexistent_project(
    client,
    authenticate,
):
    """I verify that sprint creation requires an existing project."""

    headers = authenticate(ADMIN)

    response = client.post(
        SPRINTS_URL,
        json={
            "project_id": str(UNKNOWN_ID),
            **SPRINT_PAYLOAD,
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_nonexistent_sprint(client, authenticate):
    """I verify that retrieving an unknown sprint returns HTTP 404."""

    headers = authenticate(ADMIN)

    response = client.get(
        f"{SPRINTS_URL}/{UNKNOWN_ID}",
        headers=headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_nonexistent_sprint(client, authenticate):
    """I verify that updating an unknown sprint returns HTTP 404."""

    headers = authenticate(ADMIN)

    response = client.patch(
        f"{SPRINTS_URL}/{UNKNOWN_ID}",
        json={"name": "Updated Sprint"},
        headers=headers,
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.parametrize("limit", [0, 101])
def test_reject_invalid_pagination_limit(
    client,
    authenticate,
    project_id,
    limit,
):
    """I reject pagination limits outside the allowed range."""

    headers = authenticate(ADMIN)

    response = client.get(
        SPRINTS_URL,
        params={
            "project_id": str(project_id),
            "limit": limit,
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
