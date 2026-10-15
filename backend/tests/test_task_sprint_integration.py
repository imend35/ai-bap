
"""Test Task and Sprint integration through the API."""

from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import SessionLocal
from app.main import app
from app.models import Project, Requirement, Sprint, Task, UserStory


client = TestClient(app)


def get_auth_headers() -> dict[str, str]:
    """Return valid authentication headers for API tests."""
    token = get_settings().demo_access_token.get_secret_value()
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sprint_test_data():
    """Create test projects, stories, and sprints with automatic cleanup."""
    project_ids = []

    try:
        with SessionLocal() as db:
            project = Project(
                name="Task Sprint Integration Project",
                status="active",
            )
            other_project = Project(
                name="Unrelated Sprint Project",
                status="active",
            )

            db.add_all([project, other_project])
            db.flush()

            project_ids.extend([project.id, other_project.id])

            requirement = Requirement(
                project_id=project.id,
                title="Sprint Integration Requirement",
                description="Manage task sprint assignments.",
                priority="high",
                status="approved",
            )
            db.add(requirement)
            db.flush()

            story = UserStory(
                requirement_id=requirement.id,
                title="Sprint Integration Story",
                description="As a user, I want to assign tasks to sprints.",
                acceptance_criteria=["Tasks belong to valid project sprints."],
                status="approved",
            )
            db.add(story)
            db.flush()

            sprint_one = Sprint(
                project_id=project.id,
                name="Sprint One",
                start_date="2026-10-01",
                end_date="2026-10-14",
                status="planned",
            )
            sprint_two = Sprint(
                project_id=project.id,
                name="Sprint Two",
                start_date="2026-10-15",
                end_date="2026-10-28",
                status="planned",
            )
            other_sprint = Sprint(
                project_id=other_project.id,
                name="Other Project Sprint",
                start_date="2026-10-01",
                end_date="2026-10-14",
                status="planned",
            )

            db.add_all([sprint_one, sprint_two, other_sprint])
            db.commit()

            data = {
                "story_id": str(story.id),
                "sprint_one_id": str(sprint_one.id),
                "sprint_two_id": str(sprint_two.id),
                "other_sprint_id": str(other_sprint.id),
            }

        yield data

    finally:
        # Remove the temporary projects and their related records.
        with SessionLocal() as db:
            for project_id in project_ids:
                project = db.get(Project, project_id)
                if project is not None:
                    db.delete(project)
            db.commit()


def create_test_task(story_id: str, sprint_id: str | None = None):
    """Create a task through the API."""
    payload = {
        "story_id": story_id,
        "title": "Implement Sprint Integration",
        "description": "Test sprint assignment.",
    }

    if sprint_id is not None:
        payload["sprint_id"] = sprint_id

    return client.post(
        "/api/v1/tasks",
        json=payload,
        headers=get_auth_headers(),
    )


def test_create_task_without_sprint(sprint_test_data):
    """Verify that tasks can be created without a sprint."""
    response = create_test_task(sprint_test_data["story_id"])

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["sprint_id"] is None


def test_create_task_with_valid_sprint(sprint_test_data):
    """Verify that tasks can be assigned to a project sprint."""
    response = create_test_task(
        sprint_test_data["story_id"],
        sprint_test_data["sprint_one_id"],
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["sprint_id"] == sprint_test_data["sprint_one_id"]


def test_create_task_with_nonexistent_sprint(sprint_test_data):
    """Reject task creation with an unknown sprint."""
    response = create_test_task(
        sprint_test_data["story_id"],
        str(uuid4()),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Sprint not found."


def test_create_task_with_other_project_sprint(sprint_test_data):
    """Reject a sprint belonging to another project."""
    response = create_test_task(
        sprint_test_data["story_id"],
        sprint_test_data["other_sprint_id"],
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == (
        "Sprint must belong to the same project as the task."
    )


def test_update_task_sprint(sprint_test_data):
    """Verify that an existing task can be assigned to a sprint."""
    created = create_test_task(sprint_test_data["story_id"])
    assert created.status_code == status.HTTP_201_CREATED

    task_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"sprint_id": sprint_test_data["sprint_one_id"]},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["sprint_id"] == sprint_test_data["sprint_one_id"]


def test_move_task_between_sprints(sprint_test_data):
    """Verify that a task can move between sprints in the same project."""
    created = create_test_task(
        sprint_test_data["story_id"],
        sprint_test_data["sprint_one_id"],
    )
    assert created.status_code == status.HTTP_201_CREATED

    task_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"sprint_id": sprint_test_data["sprint_two_id"]},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["sprint_id"] == sprint_test_data["sprint_two_id"]


def test_remove_task_from_sprint(sprint_test_data):
    """Verify that sprint assignment can be removed with null."""
    created = create_test_task(
        sprint_test_data["story_id"],
        sprint_test_data["sprint_one_id"],
    )
    assert created.status_code == status.HTTP_201_CREATED

    task_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"sprint_id": None},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["sprint_id"] is None


def test_update_task_with_other_project_sprint(sprint_test_data):
    """Reject assignment to a sprint from another project."""
    created = create_test_task(sprint_test_data["story_id"])
    assert created.status_code == status.HTTP_201_CREATED

    task_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"sprint_id": sprint_test_data["other_sprint_id"]},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_update_task_with_nonexistent_sprint(sprint_test_data):
    """Reject assignment to an unknown sprint."""
    created = create_test_task(sprint_test_data["story_id"])
    assert created.status_code == status.HTTP_201_CREATED

    task_id = created.json()["id"]

    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"sprint_id": str(uuid4())},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
