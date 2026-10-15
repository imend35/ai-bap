
"""Test Sprint API behavior."""

from uuid import UUID

from fastapi import status
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

from app.database import SessionLocal
from app.models import Project


client = TestClient(app)


def get_auth_headers() -> dict[str, str]:
    """Return valid authentication headers for API tests."""
    token = get_settings().demo_access_token.get_secret_value()
    return {"Authorization": f"Bearer {token}"}


def test_list_sprints_for_nonexistent_project():
    """Verify that listing sprints for an unknown project returns 404."""
    project_id = UUID("00000000-0000-0000-0000-000000000000")

    response = client.get(
        "/api/v1/sprints",
        params={"project_id": str(project_id)},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project not found."

def test_create_sprint_successfully():
    """Verify that a sprint can be created for an existing project."""
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Sprint Creation Test",
            status="planned",
        )
        db.add(project)
        db.commit()
        project_id = project.id

    try:
        response = client.post(
            "/api/v1/sprints",
            json={
                "project_id": str(project_id),
                "name": "Sprint 1 - Development",
                "start_date": "2026-10-20",
                "end_date": "2026-11-03",
            },
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_201_CREATED

        sprint = response.json()

        assert sprint["project_id"] == str(project_id)
        assert sprint["name"] == "Sprint 1 - Development"
        assert sprint["start_date"] == "2026-10-20"
        assert sprint["end_date"] == "2026-11-03"
        assert sprint["status"] == "planned"
        assert "id" in sprint

    finally:
        # Remove the temporary project and its related sprint.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()

def test_list_sprints_successfully():
    """Verify that sprints are listed for an existing project."""
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Sprint Listing Test",
            status="planned",
        )
        db.add(project)
        db.commit()
        project_id = project.id

    try:
        create_response = client.post(
            "/api/v1/sprints",
            json={
                "project_id": str(project_id),
                "name": "Sprint 1 - Listing Test",
                "start_date": "2026-10-20",
                "end_date": "2026-11-03",
            },
            headers=get_auth_headers(),
        )

        assert create_response.status_code == status.HTTP_201_CREATED
        sprint_id = create_response.json()["id"]

        response = client.get(
            "/api/v1/sprints",
            params={
                "project_id": str(project_id),
                "limit": 20,
                "offset": 0,
            },
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["total"] == 1
        assert data["limit"] == 20
        assert data["offset"] == 0
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == sprint_id
        assert data["items"][0]["project_id"] == str(project_id)
        assert data["items"][0]["name"] == "Sprint 1 - Listing Test"

    finally:
        # Remove the temporary project and its related sprint.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()

def test_update_sprint_successfully():
    """Verify that an existing sprint can be updated."""
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Sprint Update Test",
            status="planned",
        )
        db.add(project)
        db.commit()
        project_id = project.id

    try:
        create_response = client.post(
            "/api/v1/sprints",
            json={
                "project_id": str(project_id),
                "name": "Sprint 1 - Foundation",
                "start_date": "2026-10-20",
                "end_date": "2026-11-03",
            },
            headers=get_auth_headers(),
        )

        assert create_response.status_code == status.HTTP_201_CREATED
        sprint_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/sprints/{sprint_id}",
            json={
                "name": "Sprint 1 - Development",
                "status": "active",
            },
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_200_OK

        sprint = response.json()

        assert sprint["id"] == sprint_id
        assert sprint["name"] == "Sprint 1 - Development"
        assert sprint["status"] == "active"
        assert sprint["start_date"] == "2026-10-20"
        assert sprint["end_date"] == "2026-11-03"

    finally:
        # Remove the temporary project and its related sprint.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()

def test_reject_invalid_sprint_date_update():
    """Verify that invalid date updates are rejected without changing data."""
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Sprint Date Validation Test",
            status="planned",
        )
        db.add(project)
        db.commit()
        project_id = project.id

    try:
        create_response = client.post(
            "/api/v1/sprints",
            json={
                "project_id": str(project_id),
                "name": "Sprint 1 - Date Validation",
                "start_date": "2026-10-20",
                "end_date": "2026-11-03",
            },
            headers=get_auth_headers(),
        )

        assert create_response.status_code == status.HTTP_201_CREATED
        sprint_id = create_response.json()["id"]

        response = client.patch(
            f"/api/v1/sprints/{sprint_id}",
            json={"end_date": "2026-10-19"},
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == (
            "Sprint end_date must be on or after start_date."
        )

        # Verify that the rejected update did not change the sprint.
        get_response = client.get(
            f"/api/v1/sprints/{sprint_id}",
            headers=get_auth_headers(),
        )

        assert get_response.status_code == status.HTTP_200_OK

        sprint = get_response.json()

        assert sprint["start_date"] == "2026-10-20"
        assert sprint["end_date"] == "2026-11-03"
        assert sprint["status"] == "planned"

    finally:
        # Remove the temporary project and its related sprint.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()
