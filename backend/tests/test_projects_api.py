
"""I test project API operations and role-based authorization."""

from contextlib import contextmanager
from uuid import UUID, uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app
from app.models import Project
from app.models.user import User
from app.role_permissions import ADMIN, BUSINESS_ANALYST, REVIEWER
from app.security import get_current_user

client = TestClient(app)
BASE_URL = "/api/v1/projects"


@contextmanager
def authenticated_as(role=BUSINESS_ANALYST):
    """I provide a persisted authenticated user with a specific role."""

    with SessionLocal() as db:
        user = User(
            email=f"project-api-{uuid4().hex}@example.com",
            full_name="Project API Test User",
            password_hash="test-only-not-for-login",
            role=role,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id

    # I override only the user lookup for authorized API tests.
    def get_test_user():
        """I return a controlled user for role verification."""
        return user

    app.dependency_overrides[get_current_user] = get_test_user

    try:
        yield client
    finally:
        # I restore the original authentication dependency.
        app.dependency_overrides.pop(get_current_user, None)

        with SessionLocal() as db:
            persisted_user = db.get(User, user_id)
            if persisted_user is not None:
                db.delete(persisted_user)
                db.commit()


@contextmanager
def temporary_project(name, description, project_status="planned"):
    """I create a project and remove it after the test."""

    with SessionLocal() as db:
        project = Project(
            name=name,
            description=description,
            status=project_status,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id = project.id

    try:
        yield project_id
    finally:
        # I remove the temporary project from PostgreSQL.
        with SessionLocal() as db:
            project = db.get(Project, project_id)
            if project is not None:
                db.delete(project)
                db.commit()


def test_list_projects_with_valid_token():
    """I verify that an authenticated analyst can list projects."""
    with authenticated_as() as api:
        response = api.get(BASE_URL)

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)
    assert data["limit"] == 20
    assert data["offset"] == 0


def test_list_projects_without_token():
    """I reject project listing without authentication."""
    response = client.get(BASE_URL)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Missing bearer token."


def test_list_projects_with_invalid_token():
    """I reject an invalid JWT."""
    response = client.get(
        BASE_URL,
        headers={"Authorization": "Bearer invalid-demo-token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid or expired access token."


def test_list_projects_with_invalid_limit():
    """I reject invalid pagination limits."""
    with authenticated_as() as api:
        response = api.get(f"{BASE_URL}?limit=0")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_project_with_valid_token():
    """I verify that an analyst can create a persistent project."""
    with authenticated_as() as api:
        response = api.post(
            BASE_URL,
            json={
                "name": "AI BAP Integration Test",
                "description": "Temporary project for API testing",
                "status": "planned",
            },
        )

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    project_id = UUID(data["id"])

    try:
        assert data["name"] == "AI BAP Integration Test"
        assert data["status"] == "planned"
        assert data["created_at"]
        assert data["updated_at"]

        with SessionLocal() as db:
            project = db.scalar(
                select(Project).where(Project.id == project_id)
            )
            assert project is not None
            assert project.name == "AI BAP Integration Test"
    finally:
        # I remove the project even if an assertion fails.
        with SessionLocal() as db:
            project = db.get(Project, project_id)
            if project is not None:
                db.delete(project)
                db.commit()


def test_create_project_without_token():
    """I require authentication before creating a project."""
    response = client.post(
        BASE_URL,
        json={"name": "Unauthorized Project"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_project_with_invalid_token():
    """I reject project creation with an invalid JWT."""
    response = client.post(
        BASE_URL,
        headers={"Authorization": "Bearer invalid-demo-token"},
        json={"name": "Unauthorized Project"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_project_with_invalid_name():
    """I reject an empty project name."""
    with authenticated_as() as api:
        response = api.post(
            BASE_URL,
            json={"name": ""},
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_existing_project():
    """I retrieve an existing project by UUID."""
    with temporary_project(
        "AI BAP Detail Test",
        "Temporary project for detail endpoint testing",
    ) as project_id:
        with authenticated_as() as api:
            response = api.get(f"{BASE_URL}/{project_id}")

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == str(project_id)
        assert data["name"] == "AI BAP Detail Test"
        assert data["status"] == "planned"
        assert data["description"] == (
            "Temporary project for detail endpoint testing"
        )


def test_get_nonexistent_project():
    """I return HTTP 404 for a nonexistent project."""
    with authenticated_as() as api:
        response = api.get(f"{BASE_URL}/{uuid4()}")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project not found."


def test_get_project_with_invalid_uuid():
    """I reject an invalid project UUID."""
    with authenticated_as() as api:
        response = api.get(f"{BASE_URL}/not-a-valid-uuid")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_project_without_token():
    """I require authentication for project details."""
    response = client.get(f"{BASE_URL}/{uuid4()}")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_existing_project():
    """I verify that an analyst can update a project."""
    with temporary_project(
        "AI BAP Update Test",
        "Original description",
    ) as project_id:
        with authenticated_as() as api:
            response = api.patch(
                f"{BASE_URL}/{project_id}",
                json={"status": "active"},
            )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert data["id"] == str(project_id)
        assert data["name"] == "AI BAP Update Test"
        assert data["description"] == "Original description"
        assert data["status"] == "active"

        with SessionLocal() as db:
            project = db.get(Project, project_id)
            assert project is not None
            assert project.status == "active"
            assert project.name == "AI BAP Update Test"


def test_update_nonexistent_project():
    """I return HTTP 404 when updating a nonexistent project."""
    with authenticated_as() as api:
        response = api.patch(
            f"{BASE_URL}/{uuid4()}",
            json={"status": "active"},
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project not found."


def test_update_project_with_empty_payload():
    """I reject an empty project update."""
    with authenticated_as() as api:
        response = api.patch(
            f"{BASE_URL}/{uuid4()}",
            json={},
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_project_with_invalid_status():
    """I reject unsupported project statuses."""
    with authenticated_as() as api:
        response = api.patch(
            f"{BASE_URL}/{uuid4()}",
            json={"status": "invalid_status"},
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_project_without_token():
    """I require authentication for project updates."""
    response = client.patch(
        f"{BASE_URL}/{uuid4()}",
        json={"status": "active"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("role", [ADMIN, BUSINESS_ANALYST, REVIEWER])
def test_all_roles_can_list_projects(role):
    """I allow every supported role to list projects."""
    with authenticated_as(role) as api:
        response = api.get(BASE_URL)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.parametrize("role", [ADMIN, BUSINESS_ANALYST])
def test_admin_and_analyst_can_create_projects(role):
    """I allow admins and analysts to create projects."""
    with authenticated_as(role) as api:
        response = api.post(
            BASE_URL,
            json={"name": f"Role Test {uuid4().hex[:8]}"},
        )

    assert response.status_code == status.HTTP_201_CREATED

    # I remove the project created for role verification.
    project_id = UUID(response.json()["id"])

    with SessionLocal() as db:
        project = db.get(Project, project_id)
        if project is not None:
            db.delete(project)
            db.commit()


def test_reviewer_cannot_create_project():
    """I prevent reviewers from creating projects."""
    with authenticated_as(REVIEWER) as api:
        response = api.post(
            BASE_URL,
            json={"name": "Reviewer Restricted Project"},
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_reviewer_cannot_update_project():
    """I prevent reviewers from updating projects."""
    with authenticated_as(REVIEWER) as api:
        response = api.patch(
            f"{BASE_URL}/{uuid4()}",
            json={"status": "active"},
        )

    assert response.status_code == status.HTTP_403_FORBIDDEN
