
"""Test project API authentication and pagination behavior."""

from uuid import UUID

from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import get_settings
from app.database import SessionLocal
from app.main import app
from app.models import Project

client = TestClient(app)


def test_list_projects_with_valid_token():
    """Verify that authorized requests return a paginated project list."""
    token = get_settings().demo_access_token.get_secret_value()

    response = client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)
    assert data["limit"] == 20
    assert data["offset"] == 0


def test_list_projects_without_token():
    """Verify that requests without a bearer token are rejected."""
    response = client.get("/api/v1/projects")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Missing bearer token."


def test_list_projects_with_invalid_token():
    """Verify that requests with an invalid bearer token are rejected."""
    response = client.get(
        "/api/v1/projects",
        headers={"Authorization": "Bearer invalid-demo-token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Invalid bearer token."


def test_list_projects_with_invalid_limit():
    """Verify that invalid pagination limits are rejected."""
    token = get_settings().demo_access_token.get_secret_value()

    response = client.get(
        "/api/v1/projects?limit=0",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_project_with_valid_token():
    """Verify that a project is created and persisted successfully."""
    token = get_settings().demo_access_token.get_secret_value()

    response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "name": "AI BAP Integration Test",
            "description": "Temporary project for API testing",
            "status": "planned",
        },
    )

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    project_id = UUID(data["id"])

    assert data["name"] == "AI BAP Integration Test"
    assert data["status"] == "planned"
    assert data["created_at"]
    assert data["updated_at"]

    with SessionLocal() as db:
        try:
            project = db.scalar(
                select(Project).where(Project.id == project_id)
            )

            assert project is not None
            assert project.name == "AI BAP Integration Test"
        finally:
            # Remove the temporary project after verification.
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()


def test_create_project_without_token():
    """Verify that project creation requires authentication."""
    response = client.post(
        "/api/v1/projects",
        json={"name": "Unauthorized Project"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_project_with_invalid_token():
    """Verify that invalid credentials cannot create projects."""
    response = client.post(
        "/api/v1/projects",
        headers={"Authorization": "Bearer invalid-demo-token"},
        json={"name": "Unauthorized Project"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_project_with_invalid_name():
    """Verify that project creation rejects an empty name."""
    token = get_settings().demo_access_token.get_secret_value()

    response = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": ""},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_existing_project():
    """Verify that an existing project can be retrieved by its UUID."""
    token = get_settings().demo_access_token.get_secret_value()

    with SessionLocal() as db:
        project = Project(
            name="AI BAP Detail Test",
            description="Temporary project for detail endpoint testing",
            status="planned",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id = project.id

    try:
        response = client.get(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["id"] == str(project_id)
        assert data["name"] == "AI BAP Detail Test"
        assert data["status"] == "planned"
        assert data["description"] == (
            "Temporary project for detail endpoint testing"
        )
    finally:
        # Remove the temporary project after the test.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()


def test_get_nonexistent_project():
    """Verify that a nonexistent project returns HTTP 404."""
    from uuid import uuid4

    token = get_settings().demo_access_token.get_secret_value()

    response = client.get(
        f"/api/v1/projects/{uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project not found."


def test_get_project_with_invalid_uuid():
    """Verify that an invalid project UUID returns HTTP 422."""
    token = get_settings().demo_access_token.get_secret_value()

    response = client.get(
        "/api/v1/projects/not-a-valid-uuid",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_project_without_token():
    """Verify that project details require authentication."""
    from uuid import uuid4

    response = client.get(
        f"/api/v1/projects/{uuid4()}",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_existing_project():
    """Verify that a partial update is persisted in PostgreSQL."""
    token = get_settings().demo_access_token.get_secret_value()

    with SessionLocal() as db:
        project = Project(
            name="AI BAP Update Test",
            description="Original description",
            status="planned",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id = project.id

    try:
        response = client.patch(
            f"/api/v1/projects/{project_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "active"},
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["id"] == str(project_id)
        assert data["name"] == "AI BAP Update Test"
        assert data["description"] == "Original description"
        assert data["status"] == "active"

        with SessionLocal() as db:
            updated_project = db.get(Project, project_id)

            assert updated_project is not None
            assert updated_project.status == "active"
            assert updated_project.name == "AI BAP Update Test"
    finally:
        # Remove the temporary project after verification.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()


def test_update_nonexistent_project():
    """Verify that updating a nonexistent project returns HTTP 404."""
    from uuid import uuid4

    token = get_settings().demo_access_token.get_secret_value()

    response = client.patch(
        f"/api/v1/projects/{uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "active"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project not found."


def test_update_project_with_empty_payload():
    """Verify that an empty update payload is rejected."""
    from uuid import uuid4

    token = get_settings().demo_access_token.get_secret_value()

    response = client.patch(
        f"/api/v1/projects/{uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
        json={},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_project_with_invalid_status():
    """Verify that unsupported project statuses are rejected."""
    from uuid import uuid4

    token = get_settings().demo_access_token.get_secret_value()

    response = client.patch(
        f"/api/v1/projects/{uuid4()}",
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "invalid_status"},
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_project_without_token():
    """Verify that project updates require authentication."""
    from uuid import uuid4

    response = client.patch(
        f"/api/v1/projects/{uuid4()}",
        json={"status": "active"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
