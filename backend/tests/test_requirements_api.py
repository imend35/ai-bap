
"""Test requirement listing API behavior."""

from uuid import uuid4

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


def test_list_requirements_for_existing_project():
    """Verify that an existing project returns a requirement list."""
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Requirements Test",
            description="Temporary project for requirement listing",
            status="planned",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id = project.id

    try:
        response = client.get(
            "/api/v1/requirements",
            params={"project_id": str(project_id)},
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["items"] == []
        assert data["total"] == 0
        assert data["limit"] == 20
        assert data["offset"] == 0
    finally:
        # Remove the temporary project after verification.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()


def test_list_requirements_for_nonexistent_project():
    """Verify that an unknown project returns HTTP 404."""
    response = client.get(
        "/api/v1/requirements",
        params={"project_id": str(uuid4())},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project not found."


def test_list_requirements_without_project_id():
    """Verify that project_id is a required query parameter."""
    response = client.get(
        "/api/v1/requirements",
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_requirements_with_invalid_project_id():
    """Verify that an invalid project UUID is rejected."""
    response = client.get(
        "/api/v1/requirements",
        params={"project_id": "invalid-uuid"},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_list_requirements_without_token():
    """Verify that requirement listing requires authentication."""
    response = client.get(
        "/api/v1/requirements",
        params={"project_id": str(uuid4())},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_requirements_with_invalid_token():
    """Verify that invalid authentication credentials are rejected."""
    response = client.get(
        "/api/v1/requirements",
        params={"project_id": str(uuid4())},
        headers={"Authorization": "Bearer invalid-demo-token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_requirements_with_invalid_limit():
    """Verify that pagination limits must be valid."""
    response = client.get(
        "/api/v1/requirements",
        params={
            "project_id": str(uuid4()),
            "limit": 0,
        },
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

def test_list_requirements_filters_by_project_and_paginates():
    """Verify project filtering, pagination, and total counts."""
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
            "/api/v1/requirements",
            params={
                "project_id": str(first_project_id),
                "limit": 1,
                "offset": 0,
            },
            headers=get_auth_headers(),
        )

        assert first_response.status_code == status.HTTP_200_OK

        first_page = first_response.json()

        assert first_page["total"] == 2
        assert first_page["limit"] == 1
        assert first_page["offset"] == 0
        assert len(first_page["items"]) == 1
        assert first_page["items"][0]["project_id"] == str(first_project_id)

        second_response = client.get(
            "/api/v1/requirements",
            params={
                "project_id": str(first_project_id),
                "limit": 1,
                "offset": 1,
            },
            headers=get_auth_headers(),
        )

        assert second_response.status_code == status.HTTP_200_OK

        second_page = second_response.json()

        assert second_page["total"] == 2
        assert second_page["offset"] == 1
        assert len(second_page["items"]) == 1
        assert second_page["items"][0]["project_id"] == str(first_project_id)

        assert first_page["items"][0]["id"] != second_page["items"][0]["id"]

        other_response = client.get(
            "/api/v1/requirements",
            params={"project_id": str(second_project_id)},
            headers=get_auth_headers(),
        )

        assert other_response.status_code == status.HTTP_200_OK

        other_page = other_response.json()

        assert other_page["total"] == 1
        assert len(other_page["items"]) == 1
        assert other_page["items"][0]["project_id"] == str(second_project_id)

    finally:
        # Remove temporary projects and their associated requirements.
        with SessionLocal() as db:
            for project_id in (first_project_id, second_project_id):
                project = db.get(Project, project_id)

                if project is not None:
                    db.delete(project)

            db.commit()


def test_create_requirement_successfully():
    """Verify that a requirement is created and stored in PostgreSQL."""
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Requirement Creation Test",
            status="planned",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id = project.id

    try:
        response = client.post(
            "/api/v1/requirements",
            json={
                "project_id": str(project_id),
                "title": "User Authentication",
                "description": "Users must sign in securely.",
                "priority": "high",
                "status": "draft",
            },
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()

        assert data["project_id"] == str(project_id)
        assert data["title"] == "User Authentication"
        assert data["description"] == "Users must sign in securely."
        assert data["priority"] == "high"
        assert data["status"] == "draft"
        assert data["id"]
        assert data["created_at"]
        assert data["updated_at"]

        # Verify that the requirement was persisted in PostgreSQL.
        with SessionLocal() as db:
            requirement = db.get(Requirement, data["id"])

            assert requirement is not None
            assert requirement.project_id == project_id
            assert requirement.title == "User Authentication"

    finally:
        # Remove the temporary project and its requirements.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()


def test_create_requirement_with_default_values():
    """Verify that omitted priority and status use default values."""
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Requirement Defaults Test",
            status="planned",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        project_id = project.id

    try:
        response = client.post(
            "/api/v1/requirements",
            json={
                "project_id": str(project_id),
                "title": "Generate User Stories",
                "description": "The system must generate user stories.",
            },
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["priority"] == "medium"
        assert response.json()["status"] == "draft"

    finally:
        # Remove temporary test data.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()


def test_create_requirement_for_nonexistent_project():
    """Verify that an unknown project returns HTTP 404."""
    response = client.post(
        "/api/v1/requirements",
        json={
            "project_id": str(uuid4()),
            "title": "User Authentication",
            "description": "Users must sign in securely.",
        },
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project not found."


def test_create_requirement_without_project_id():
    """Verify that project_id is required in the request body."""
    response = client.post(
        "/api/v1/requirements",
        json={
            "title": "User Authentication",
            "description": "Users must sign in securely.",
        },
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_requirement_with_invalid_priority():
    """Verify that unsupported priority values are rejected."""
    response = client.post(
        "/api/v1/requirements",
        json={
            "project_id": str(uuid4()),
            "title": "User Authentication",
            "description": "Users must sign in securely.",
            "priority": "urgent",
        },
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_requirement_with_long_description():
    """Verify that descriptions exceeding 5000 characters are rejected."""
    response = client.post(
        "/api/v1/requirements",
        json={
            "project_id": str(uuid4()),
            "title": "User Authentication",
            "description": "A" * 5001,
        },
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_requirement_without_token():
    """Verify that requirement creation requires authentication."""
    response = client.post(
        "/api/v1/requirements",
        json={
            "project_id": str(uuid4()),
            "title": "User Authentication",
            "description": "Users must sign in securely.",
        },
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_requirement_with_invalid_token():
    """Verify that invalid credentials are rejected."""
    response = client.post(
        "/api/v1/requirements",
        json={
            "project_id": str(uuid4()),
            "title": "User Authentication",
            "description": "Users must sign in securely.",
        },
        headers={"Authorization": "Bearer invalid-demo-token"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_requirement_successfully():
    """Verify that an existing requirement can be retrieved by ID."""
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Requirement Detail Test",
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
            f"/api/v1/requirements/{requirement_id}",
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["id"] == str(requirement_id)
        assert data["project_id"] == str(project_id)
        assert data["title"] == "User Authentication"
        assert data["description"] == "Users must sign in securely."
        assert data["priority"] == "high"
        assert data["status"] == "draft"
        assert data["created_at"]
        assert data["updated_at"]

    finally:
        # Remove the temporary project and its requirements.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()


def test_get_nonexistent_requirement():
    """Verify that an unknown requirement returns HTTP 404."""
    response = client.get(
        f"/api/v1/requirements/{uuid4()}",
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Requirement not found."


def test_get_requirement_with_invalid_uuid():
    """Verify that an invalid requirement UUID returns HTTP 422."""
    response = client.get(
        "/api/v1/requirements/invalid-uuid",
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_requirement_without_token():
    """Verify that requirement details require authentication."""
    response = client.get(
        f"/api/v1/requirements/{uuid4()}",
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_requirement_partially_and_persist_changes():
    """Verify partial updates preserve other fields and persist in PostgreSQL."""
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Requirement Update Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="User Authentication",
            description="Users must sign in securely.",
            priority="medium",
            status="draft",
        )
        db.add(requirement)
        db.commit()

        project_id = project.id
        requirement_id = requirement.id

    try:
        response = client.patch(
            f"/api/v1/requirements/{requirement_id}",
            json={
                "priority": "critical",
                "status": "in_review",
            },
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["id"] == str(requirement_id)
        assert data["project_id"] == str(project_id)
        assert data["title"] == "User Authentication"
        assert data["description"] == "Users must sign in securely."
        assert data["priority"] == "critical"
        assert data["status"] == "in_review"

        # Verify that the changes were persisted in PostgreSQL.
        with SessionLocal() as db:
            saved_requirement = db.get(Requirement, requirement_id)

            assert saved_requirement is not None
            assert saved_requirement.project_id == project_id
            assert saved_requirement.title == "User Authentication"
            assert saved_requirement.description == "Users must sign in securely."
            assert saved_requirement.priority == "critical"
            assert saved_requirement.status == "in_review"

    finally:
        # Remove the temporary project and its requirements.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()


def test_update_nonexistent_requirement():
    """Verify that updating an unknown requirement returns HTTP 404."""
    response = client.patch(
        f"/api/v1/requirements/{uuid4()}",
        json={"priority": "high"},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Requirement not found."


def test_update_requirement_with_invalid_uuid():
    """Verify that an invalid requirement UUID returns HTTP 422."""
    response = client.patch(
        "/api/v1/requirements/invalid-uuid",
        json={"priority": "high"},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_requirement_with_empty_payload():
    """Verify that empty PATCH requests are rejected."""
    response = client.patch(
        f"/api/v1/requirements/{uuid4()}",
        json={},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_requirement_with_invalid_priority():
    """Verify that unsupported priority values are rejected."""
    response = client.patch(
        f"/api/v1/requirements/{uuid4()}",
        json={"priority": "urgent"},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_requirement_with_null_status():
    """Verify that null values cannot replace required fields."""
    response = client.patch(
        f"/api/v1/requirements/{uuid4()}",
        json={"status": None},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_update_requirement_without_token():
    """Verify that updating requirements requires authentication."""
    response = client.patch(
        f"/api/v1/requirements/{uuid4()}",
        json={"priority": "high"},
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
