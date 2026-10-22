
"""I test Task and Sprint integration through the secured API."""

from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Project, Requirement, Sprint, UserStory
from app.role_permissions import ADMIN
from app.security import get_current_user

TASKS_URL = "/api/v1/tasks"


class MockUser:
    """I represent an authenticated administrator in integration tests."""

    def __init__(self):
        self.id = uuid4()
        self.role = ADMIN
        self.is_active = True


@pytest.fixture
def client():
    """I create a test client with isolated administrator authentication."""

    # I simulate an authenticated administrator for Task API requests.
    app.dependency_overrides[get_current_user] = lambda: MockUser()

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        # I remove the authentication override after every test.
        app.dependency_overrides.pop(get_current_user, None)


def get_auth_headers() -> dict[str, str]:
    """I provide a test authorization header for authenticated requests."""

    return {"Authorization": "Bearer test-jwt-token"}


@pytest.fixture
def sprint_test_data():
    """I create test projects, stories, and sprints with automatic cleanup."""

    project_ids = []

    try:
        with SessionLocal() as db:
            # I create separate projects to verify sprint ownership.
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

            # I create a requirement associated with the primary project.
            requirement = Requirement(
                project_id=project.id,
                title="Sprint Integration Requirement",
                description="Manage task sprint assignments.",
                priority="high",
                status="approved",
            )
            db.add(requirement)
            db.flush()

            # I approve the user story to allow task creation.
            story = UserStory(
                requirement_id=requirement.id,
                title="Sprint Integration Story",
                description="As a user, I want to assign tasks to sprints.",
                acceptance_criteria=[
                    "Tasks belong to valid project sprints."
                ],
                status="approved",
            )
            db.add(story)
            db.flush()

            # I create two sprints belonging to the primary project.
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

            # I create another sprint to test cross-project restrictions.
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
        # I delete temporary projects and their related records.
        with SessionLocal() as db:
            for project_id in project_ids:
                project = db.get(Project, project_id)

                if project is not None:
                    db.delete(project)

            db.commit()


def create_test_task(
    client: TestClient,
    story_id: str,
    sprint_id: str | None = None,
):
    """I create a task through the authenticated Task API."""

    payload = {
        "story_id": story_id,
        "title": "Implement Sprint Integration",
        "description": "Test sprint assignment.",
    }

    # I include the sprint only when an assignment is requested.
    if sprint_id is not None:
        payload["sprint_id"] = sprint_id

    return client.post(
        TASKS_URL,
        json=payload,
        headers=get_auth_headers(),
    )


def test_create_task_without_sprint(client, sprint_test_data):
    """I verify that tasks can be created without a sprint."""

    response = create_test_task(
        client,
        sprint_test_data["story_id"],
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["sprint_id"] is None


def test_create_task_with_valid_sprint(client, sprint_test_data):
    """I verify that tasks can be assigned to a project sprint."""

    response = create_test_task(
        client,
        sprint_test_data["story_id"],
        sprint_test_data["sprint_one_id"],
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["sprint_id"] == sprint_test_data["sprint_one_id"]


def test_create_task_with_nonexistent_sprint(client, sprint_test_data):
    """I reject task creation with an unknown sprint."""

    response = create_test_task(
        client,
        sprint_test_data["story_id"],
        str(uuid4()),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Sprint not found."


def test_create_task_with_other_project_sprint(client, sprint_test_data):
    """I reject sprint assignments belonging to another project."""

    response = create_test_task(
        client,
        sprint_test_data["story_id"],
        sprint_test_data["other_sprint_id"],
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == (
        "Sprint must belong to the same project as the task."
    )


def test_update_task_sprint(client, sprint_test_data):
    """I verify that an existing task can be assigned to a sprint."""

    created = create_test_task(
        client,
        sprint_test_data["story_id"],
    )
    assert created.status_code == status.HTTP_201_CREATED

    task_id = created.json()["id"]

    response = client.patch(
        f"{TASKS_URL}/{task_id}",
        json={"sprint_id": sprint_test_data["sprint_one_id"]},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["sprint_id"] == sprint_test_data["sprint_one_id"]


def test_move_task_between_sprints(client, sprint_test_data):
    """I verify that tasks can move between sprints in the same project."""

    created = create_test_task(
        client,
        sprint_test_data["story_id"],
        sprint_test_data["sprint_one_id"],
    )
    assert created.status_code == status.HTTP_201_CREATED

    task_id = created.json()["id"]

    response = client.patch(
        f"{TASKS_URL}/{task_id}",
        json={"sprint_id": sprint_test_data["sprint_two_id"]},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["sprint_id"] == sprint_test_data["sprint_two_id"]


def test_remove_task_from_sprint(client, sprint_test_data):
    """I verify that sprint assignments can be removed using null."""

    created = create_test_task(
        client,
        sprint_test_data["story_id"],
        sprint_test_data["sprint_one_id"],
    )
    assert created.status_code == status.HTTP_201_CREATED

    task_id = created.json()["id"]

    response = client.patch(
        f"{TASKS_URL}/{task_id}",
        json={"sprint_id": None},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["sprint_id"] is None


def test_update_task_with_other_project_sprint(client, sprint_test_data):
    """I reject updates assigning tasks to another project's sprint."""

    created = create_test_task(
        client,
        sprint_test_data["story_id"],
    )
    assert created.status_code == status.HTTP_201_CREATED

    task_id = created.json()["id"]

    response = client.patch(
        f"{TASKS_URL}/{task_id}",
        json={"sprint_id": sprint_test_data["other_sprint_id"]},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == (
        "Sprint must belong to the same project as the task."
    )


def test_update_task_with_nonexistent_sprint(client, sprint_test_data):
    """I reject updates assigning tasks to nonexistent sprints."""

    created = create_test_task(
        client,
        sprint_test_data["story_id"],
    )
    assert created.status_code == status.HTTP_201_CREATED

    task_id = created.json()["id"]

    response = client.patch(
        f"{TASKS_URL}/{task_id}",
        json={"sprint_id": str(uuid4())},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Sprint not found."
