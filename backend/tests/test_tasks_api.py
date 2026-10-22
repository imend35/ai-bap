
"""I test Task API behavior, business rules, and role-based access."""

from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.main import app
from app.models import Project, Requirement, Task, UserStory
from app.role_permissions import ADMIN, BUSINESS_ANALYST, REVIEWER
from app.security import get_current_user

TASKS_URL = "/api/v1/tasks"


class MockUser:
    """I represent an authenticated user with a selected role."""

    def __init__(self, role: str):
        self.id = uuid4()
        self.role = role
        self.is_active = True


@pytest.fixture
def client():
    """I create a test client with isolated authentication overrides."""

    # I remove any authentication override left by another test.
    app.dependency_overrides.pop(get_current_user, None)

    with TestClient(app) as test_client:
        yield test_client

    # I restore the original authentication behavior after the test.
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def authenticate():
    """I simulate an authenticated user with a specified role."""

    def set_role(role: str):
        user = MockUser(role)

        # I override only the current-user dependency.
        app.dependency_overrides[get_current_user] = lambda: user

        return {"Authorization": "Bearer test-jwt-token"}

    yield set_role

    # I prevent mocked roles from affecting subsequent tests.
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def story_factory():
    """I create temporary project and user-story records."""

    project_ids = []

    def create_story(story_status="approved"):
        with SessionLocal() as db:
            project = Project(
                name=f"AI BAP Task Test {uuid4()}",
                status="planned",
            )
            db.add(project)
            db.flush()

            requirement = Requirement(
                project_id=project.id,
                title="Task Management Requirement",
                description="I manage tasks linked to user stories.",
                priority="high",
                status="draft",
            )
            db.add(requirement)
            db.flush()

            story = UserStory(
                requirement_id=requirement.id,
                title="Task Management User Story",
                description="As a user, I want to manage development tasks.",
                acceptance_criteria=["Tasks follow approval rules."],
                status=story_status,
            )
            db.add(story)
            db.commit()

            project_id = project.id
            story_id = story.id
            project_ids.append(project_id)

        return project_id, story_id

    yield create_story

    # I delete all temporary projects and their related test records.
    with SessionLocal() as db:
        for project_id in project_ids:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)

        db.commit()


@pytest.fixture
def approved_story(story_factory):
    """I create an approved user story for task operations."""
    return story_factory("approved")


@pytest.fixture
def task_factory():
    """I create tasks directly in PostgreSQL for API tests."""

    def create_task(story_id, title="Implement Task API", task_status="todo"):
        with SessionLocal() as db:
            task = Task(
                story_id=story_id,
                title=title,
                description="Develop and test the Task API.",
                status=task_status,
            )
            db.add(task)
            db.commit()
            return task.id

    return create_task


@pytest.mark.parametrize("story_status", ["draft", "in_review", "rejected"])
def test_create_task_for_unapproved_user_story(
    client,
    authenticate,
    story_factory,
    story_status,
):
    """I reject task creation for user stories without approval."""

    _, story_id = story_factory(story_status)
    headers = authenticate(ADMIN)

    response = client.post(
        TASKS_URL,
        json={
            "story_id": str(story_id),
            "title": "Implement Task API",
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == (
        "Tasks can only be created for approved user stories."
    )


@pytest.mark.parametrize("role", [ADMIN, BUSINESS_ANALYST])
def test_create_task_for_approved_user_story(
    client,
    authenticate,
    approved_story,
    role,
):
    """I verify that permitted roles can create tasks after approval."""

    _, story_id = approved_story
    headers = authenticate(role)

    response = client.post(
        TASKS_URL,
        json={
            "story_id": str(story_id),
            "title": "Implement Task API",
            "description": "Develop the task creation endpoint.",
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()

    assert data["story_id"] == str(story_id)
    assert data["title"] == "Implement Task API"
    assert data["description"] == "Develop the task creation endpoint."
    assert data["status"] == "todo"
    assert data["id"]
    assert data["created_at"]
    assert data["updated_at"]

    # I verify that the task was persisted in PostgreSQL.
    with SessionLocal() as db:
        saved_task = db.get(Task, data["id"])

        assert saved_task is not None
        assert saved_task.story_id == story_id
        assert saved_task.title == "Implement Task API"
        assert saved_task.status == "todo"


@pytest.mark.parametrize("role", [ADMIN, BUSINESS_ANALYST, REVIEWER])
def test_list_tasks_for_existing_user_story(
    client,
    authenticate,
    approved_story,
    role,
):
    """I verify that permitted roles can view an empty task list."""

    _, story_id = approved_story
    headers = authenticate(role)

    response = client.get(
        TASKS_URL,
        params={"story_id": str(story_id)},
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 20
    assert data["offset"] == 0


def test_list_tasks_with_pagination(
    client,
    authenticate,
    approved_story,
    task_factory,
):
    """I verify task totals, pagination, and story relationships."""

    _, story_id = approved_story
    headers = authenticate(ADMIN)

    # I create three tasks to verify the requested page size.
    for index in range(1, 4):
        task_factory(
            story_id,
            title=f"Development Task {index}",
        )

    response = client.get(
        TASKS_URL,
        params={
            "story_id": str(story_id),
            "limit": 2,
            "offset": 1,
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["total"] == 3
    assert data["limit"] == 2
    assert data["offset"] == 1
    assert len(data["items"]) == 2

    # I verify that every returned task belongs to the selected story.
    for task in data["items"]:
        assert task["story_id"] == str(story_id)
        assert task["id"]
        assert task["title"]
        assert task["status"] == "todo"


@pytest.mark.parametrize("role", [ADMIN, BUSINESS_ANALYST, REVIEWER])
def test_get_task_successfully(
    client,
    authenticate,
    approved_story,
    task_factory,
    role,
):
    """I verify that permitted roles can retrieve task details."""

    _, story_id = approved_story
    task_id = task_factory(
        story_id,
        title="Implement Task Detail API",
        task_status="in_progress",
    )
    headers = authenticate(role)

    response = client.get(
        f"{TASKS_URL}/{task_id}",
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == str(task_id)
    assert data["story_id"] == str(story_id)
    assert data["title"] == "Implement Task Detail API"
    assert data["status"] == "in_progress"
    assert data["created_at"]
    assert data["updated_at"]


@pytest.mark.parametrize("role", [ADMIN, BUSINESS_ANALYST])
def test_update_task_partially_and_persist_changes(
    client,
    authenticate,
    approved_story,
    task_factory,
    role,
):
    """I verify partial task updates and database persistence."""

    _, story_id = approved_story
    task_id = task_factory(
        story_id,
        title="Implement Task Update API",
    )
    headers = authenticate(role)

    response = client.patch(
        f"{TASKS_URL}/{task_id}",
        json={"status": "in_progress"},
        headers=headers,
    )

    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["id"] == str(task_id)
    assert data["story_id"] == str(story_id)
    assert data["title"] == "Implement Task Update API"
    assert data["description"] == "Develop and test the Task API."
    assert data["status"] == "in_progress"

    # I verify that the updated values were saved in PostgreSQL.
    with SessionLocal() as db:
        saved_task = db.get(Task, task_id)

        assert saved_task is not None
        assert saved_task.status == "in_progress"
        assert saved_task.title == "Implement Task Update API"
        assert saved_task.story_id == story_id


def test_update_task_with_invalid_status(client, authenticate):
    """I reject unsupported task status values."""

    headers = authenticate(ADMIN)

    response = client.patch(
        f"{TASKS_URL}/{uuid4()}",
        json={"status": "cancelled"},
        headers=headers,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert any(
        "status" in error["loc"]
        for error in response.json()["detail"]
    )


@pytest.mark.parametrize("payload", [{}, {"status": None}])
def test_update_task_with_invalid_payload(
    client,
    authenticate,
    payload,
):
    """I reject empty or invalid task updates."""

    headers = authenticate(ADMIN)

    response = client.patch(
        f"{TASKS_URL}/{uuid4()}",
        json=payload,
        headers=headers,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["detail"]


@pytest.mark.parametrize("http_method", ["GET", "PATCH"])
def test_nonexistent_task_returns_404(
    client,
    authenticate,
    http_method,
):
    """I return HTTP 404 for unknown task identifiers."""

    headers = authenticate(ADMIN)
    task_id = uuid4()

    if http_method == "GET":
        response = client.get(
            f"{TASKS_URL}/{task_id}",
            headers=headers,
        )
    else:
        response = client.patch(
            f"{TASKS_URL}/{task_id}",
            json={"status": "in_progress"},
            headers=headers,
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Task not found."


@pytest.mark.parametrize("http_method", ["GET", "PATCH"])
def test_invalid_task_uuid_returns_422(
    client,
    authenticate,
    http_method,
):
    """I reject malformed task UUID values."""

    headers = authenticate(ADMIN)

    if http_method == "GET":
        response = client.get(
            f"{TASKS_URL}/invalid-uuid",
            headers=headers,
        )
    else:
        response = client.patch(
            f"{TASKS_URL}/invalid-uuid",
            json={"status": "in_progress"},
            headers=headers,
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["detail"]


@pytest.mark.parametrize(
    "http_method,endpoint",
    [
        ("GET", TASKS_URL),
        ("POST", TASKS_URL),
        ("GET", f"{TASKS_URL}/{{task_id}}"),
        ("PATCH", f"{TASKS_URL}/{{task_id}}"),
    ],
)
def test_task_endpoints_without_token(
    client,
    http_method,
    endpoint,
):
    """I verify that all task endpoints require authentication."""

    endpoint = endpoint.replace("{task_id}", str(uuid4()))

    if http_method == "GET":
        response = client.get(
            endpoint,
            params={"story_id": str(uuid4())}
            if endpoint == TASKS_URL
            else None,
        )
    elif http_method == "POST":
        response = client.post(
            endpoint,
            json={
                "story_id": str(uuid4()),
                "title": "Unauthorized Task",
            },
        )
    else:
        response = client.patch(
            endpoint,
            json={"status": "in_progress"},
        )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("http_method", ["GET", "POST"])
def test_task_api_with_nonexistent_user_story(
    client,
    authenticate,
    http_method,
):
    """I reject operations referencing nonexistent user stories."""

    headers = authenticate(ADMIN)
    story_id = uuid4()

    if http_method == "GET":
        response = client.get(
            TASKS_URL,
            params={"story_id": str(story_id)},
            headers=headers,
        )
    else:
        response = client.post(
            TASKS_URL,
            json={
                "story_id": str(story_id),
                "title": "Implement Task API",
            },
            headers=headers,
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User Story not found."


@pytest.mark.parametrize("http_method", ["GET", "POST"])
def test_task_api_without_story_id(
    client,
    authenticate,
    http_method,
):
    """I verify that task operations require a user-story identifier."""

    headers = authenticate(ADMIN)

    if http_method == "GET":
        response = client.get(
            TASKS_URL,
            headers=headers,
        )
    else:
        response = client.post(
            TASKS_URL,
            json={
                "title": "Task Without User Story",
                "description": "This task has no story reference.",
            },
            headers=headers,
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert any(
        "story_id" in error["loc"]
        for error in response.json()["detail"]
    )


@pytest.mark.parametrize(
    "pagination_params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
    ],
)
def test_list_tasks_with_invalid_pagination(
    client,
    authenticate,
    pagination_params,
):
    """I reject pagination parameters outside the permitted range."""

    headers = authenticate(ADMIN)

    response = client.get(
        TASKS_URL,
        params={
            "story_id": str(uuid4()),
            **pagination_params,
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["detail"]


def test_reviewer_cannot_create_task(
    client,
    authenticate,
    approved_story,
):
    """I prevent reviewers from creating tasks."""

    _, story_id = approved_story
    headers = authenticate(REVIEWER)

    response = client.post(
        TASKS_URL,
        json={
            "story_id": str(story_id),
            "title": "Unauthorized Task",
        },
        headers=headers,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_reviewer_cannot_update_task(
    client,
    authenticate,
    approved_story,
    task_factory,
):
    """I prevent reviewers from modifying existing tasks."""

    _, story_id = approved_story
    task_id = task_factory(story_id)
    headers = authenticate(REVIEWER)

    response = client.patch(
        f"{TASKS_URL}/{task_id}",
        json={"status": "in_progress"},
        headers=headers,
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN

    # I verify that the rejected update did not modify the task.
    with SessionLocal() as db:
        saved_task = db.get(Task, task_id)

        assert saved_task is not None
        assert saved_task.status == "todo"
