
"""Test Task API behavior."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import SessionLocal
from app.main import app
from app.models import Project, Requirement, UserStory

client = TestClient(app)


def get_auth_headers() -> dict[str, str]:
    """Return valid authentication headers for API tests."""
    token = get_settings().demo_access_token.get_secret_value()
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    "story_status",
    ["draft", "in_review", "rejected"],
)
def test_create_task_for_unapproved_user_story(story_status: str):
    """Verify that tasks cannot be created for unapproved user stories."""
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Task Approval Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="Task Approval Requirement",
            description="Tasks require approved user stories.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.flush()

        story = UserStory(
            requirement_id=requirement.id,
            title="Task Approval Story",
            description="As a user, I want approved tasks.",
            acceptance_criteria=["The story must be approved."],
            status=story_status,
        )
        db.add(story)
        db.commit()

        project_id = project.id
        story_id = story.id

    try:
        response = client.post(
            "/api/v1/tasks",
            json={
                "story_id": str(story_id),
                "title": "Implement Task API",
            },
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == (
            "Tasks can only be created for approved user stories."
        )

    finally:
        # Remove temporary test records and their related data.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()

def test_create_task_for_approved_user_story():
    """Verify that an approved user story allows task creation."""
    from app.models import Task

    with SessionLocal() as db:
        project = Project(
            name="AI BAP Approved Task Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="Approved Task Requirement",
            description="Approved user stories can have tasks.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.flush()

        story = UserStory(
            requirement_id=requirement.id,
            title="Approved Task Story",
            description="As a user, I want to manage development tasks.",
            acceptance_criteria=["Tasks can be created after approval."],
            status="approved",
        )
        db.add(story)
        db.commit()

        project_id = project.id
        story_id = story.id

    try:
        response = client.post(
            "/api/v1/tasks",
            json={
                "story_id": str(story_id),
                "title": "Implement Task API",
                "description": "Develop the task creation endpoint.",
            },
            headers=get_auth_headers(),
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

        # Verify that the task was persisted in PostgreSQL.
        with SessionLocal() as db:
            saved_task = db.get(Task, data["id"])

            assert saved_task is not None
            assert saved_task.story_id == story_id
            assert saved_task.title == "Implement Task API"
            assert saved_task.status == "todo"

    finally:
        # Remove temporary test records and their related data.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()

def test_list_tasks_for_existing_user_story():
    """Verify that a user story without tasks returns an empty task list."""
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Task Listing Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="Task Listing Requirement",
            description="Users can view tasks linked to a user story.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.flush()

        story = UserStory(
            requirement_id=requirement.id,
            title="View Story Tasks",
            description="As a user, I want to view related tasks.",
            acceptance_criteria=["Tasks are listed for the selected story."],
            status="approved",
        )
        db.add(story)
        db.commit()

        project_id = project.id
        story_id = story.id

    try:
        response = client.get(
            "/api/v1/tasks",
            params={"story_id": str(story_id)},
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["items"] == []
        assert data["total"] == 0
        assert data["limit"] == 20
        assert data["offset"] == 0

    finally:
        # Remove temporary test records and their related data.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()

def test_list_tasks_with_pagination():
    """Verify task listing returns the correct total and pagination."""
    from app.models import Task

    with SessionLocal() as db:
        project = Project(
            name="AI BAP Task Pagination Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="Task Pagination Requirement",
            description="Users can browse tasks with pagination.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.flush()

        story = UserStory(
            requirement_id=requirement.id,
            title="Browse Story Tasks",
            description="As a user, I want to browse development tasks.",
            acceptance_criteria=["Tasks support pagination."],
            status="approved",
        )
        db.add(story)
        db.flush()

        for index in range(1, 4):
            db.add(
                Task(
                    story_id=story.id,
                    title=f"Development Task {index}",
                    description=f"Task number {index}.",
                    status="todo",
                )
            )

        db.commit()
        project_id = project.id
        story_id = story.id

    try:
        response = client.get(
            "/api/v1/tasks",
            params={
                "story_id": str(story_id),
                "limit": 2,
                "offset": 1,
            },
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["total"] == 3
        assert data["limit"] == 2
        assert data["offset"] == 1
        assert len(data["items"]) == 2

        # Verify that every returned task belongs to the selected story.
        for task in data["items"]:
            assert task["story_id"] == str(story_id)
            assert task["id"]
            assert task["title"]
            assert task["status"] == "todo"

    finally:
        # Remove temporary test records and their related data.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()

def test_get_task_successfully():
    """Verify that an existing task can be retrieved by ID."""
    from app.models import Task

    with SessionLocal() as db:
        project = Project(
            name="AI BAP Task Detail Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="Task Detail Requirement",
            description="Users can view task details.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.flush()

        story = UserStory(
            requirement_id=requirement.id,
            title="View Task Details",
            description="As a user, I want to view task details.",
            acceptance_criteria=["Task details are displayed correctly."],
            status="approved",
        )
        db.add(story)
        db.flush()

        task = Task(
            story_id=story.id,
            title="Implement Task Detail API",
            description="Retrieve a task using its unique ID.",
            status="in_progress",
        )
        db.add(task)
        db.commit()

        project_id = project.id
        story_id = story.id
        task_id = task.id

    try:
        response = client.get(
            f"/api/v1/tasks/{task_id}",
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["id"] == str(task_id)
        assert data["story_id"] == str(story_id)
        assert data["title"] == "Implement Task Detail API"
        assert data["description"] == "Retrieve a task using its unique ID."
        assert data["status"] == "in_progress"
        assert data["created_at"]
        assert data["updated_at"]

    finally:
        # Remove temporary test records and their related data.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()

def test_update_task_partially_and_persist_changes():
    """Verify partial task updates are persisted without changing other fields."""
    from app.models import Task

    with SessionLocal() as db:
        project = Project(
            name="AI BAP Task Update Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="Task Update Requirement",
            description="Users can update development tasks.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.flush()

        story = UserStory(
            requirement_id=requirement.id,
            title="Update Development Tasks",
            description="As a user, I want to update task progress.",
            acceptance_criteria=["Task status can be updated."],
            status="approved",
        )
        db.add(story)
        db.flush()

        task = Task(
            story_id=story.id,
            title="Implement Task Update API",
            description="Support partial task updates.",
            status="todo",
        )
        db.add(task)
        db.commit()

        project_id = project.id
        story_id = story.id
        task_id = task.id

    try:
        response = client.patch(
            f"/api/v1/tasks/{task_id}",
            json={"status": "in_progress"},
            headers=get_auth_headers(),
        )

        assert response.status_code == status.HTTP_200_OK

        data = response.json()

        assert data["id"] == str(task_id)
        assert data["story_id"] == str(story_id)
        assert data["title"] == "Implement Task Update API"
        assert data["description"] == "Support partial task updates."
        assert data["status"] == "in_progress"

        # Verify that the update was persisted in PostgreSQL.
        with SessionLocal() as db:
            saved_task = db.get(Task, task_id)

            assert saved_task is not None
            assert saved_task.status == "in_progress"
            assert saved_task.title == "Implement Task Update API"
            assert saved_task.description == "Support partial task updates."
            assert saved_task.story_id == story_id

    finally:
        # Remove temporary test records and their related data.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()

def test_update_task_with_invalid_status():
    """Verify that unsupported task statuses are rejected."""
    from uuid import uuid4

    response = client.patch(
        f"/api/v1/tasks/{uuid4()}",
        json={"status": "cancelled"},
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    errors = response.json()["detail"]

    # Verify that the validation error concerns the status field.
    assert any(
        "status" in error["loc"]
        for error in errors
    )

@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"status": None},
    ],
)
def test_update_task_with_invalid_payload(payload: dict):
    """Verify that empty and null task updates are rejected."""
    from uuid import uuid4

    response = client.patch(
        f"/api/v1/tasks/{uuid4()}",
        json=payload,
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["detail"]

@pytest.mark.parametrize(
    "http_method",
    ["GET", "PATCH"],
)
def test_nonexistent_task_returns_404(http_method: str):
    """Verify that unknown task IDs return HTTP 404."""
    from uuid import uuid4

    task_id = uuid4()

    if http_method == "GET":
        response = client.get(
            f"/api/v1/tasks/{task_id}",
            headers=get_auth_headers(),
        )
    else:
        response = client.patch(
            f"/api/v1/tasks/{task_id}",
            json={"status": "in_progress"},
            headers=get_auth_headers(),
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Task not found."

@pytest.mark.parametrize(
    "http_method",
    ["GET", "PATCH"],
)
def test_invalid_task_uuid_returns_422(http_method: str):
    """Verify that invalid task UUIDs are rejected."""
    invalid_task_id = "invalid-uuid"

    if http_method == "GET":
        response = client.get(
            f"/api/v1/tasks/{invalid_task_id}",
            headers=get_auth_headers(),
        )
    else:
        response = client.patch(
            f"/api/v1/tasks/{invalid_task_id}",
            json={"status": "in_progress"},
            headers=get_auth_headers(),
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["detail"]

@pytest.mark.parametrize(
    "http_method, endpoint",
    [
        ("GET", "/api/v1/tasks"),
        ("POST", "/api/v1/tasks"),
        ("GET", "/api/v1/tasks/{task_id}"),
        ("PATCH", "/api/v1/tasks/{task_id}"),
    ],
)
def test_task_endpoints_without_token(http_method: str, endpoint: str):
    """Verify that every Task API endpoint requires authentication."""
    from uuid import uuid4

    task_id = uuid4()
    endpoint = endpoint.replace("{task_id}", str(task_id))

    if http_method == "GET":
        response = client.get(
            endpoint,
            params={"story_id": str(uuid4())}
            if endpoint == "/api/v1/tasks"
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
    assert response.json()["detail"] == "Missing bearer token."

@pytest.mark.parametrize(
    "http_method",
    ["GET", "POST"],
)
def test_task_api_with_nonexistent_user_story(http_method: str):
    """Verify that tasks cannot reference a nonexistent user story."""
    from uuid import uuid4

    story_id = uuid4()

    if http_method == "GET":
        response = client.get(
            "/api/v1/tasks",
            params={"story_id": str(story_id)},
            headers=get_auth_headers(),
        )
    else:
        response = client.post(
            "/api/v1/tasks",
            json={
                "story_id": str(story_id),
                "title": "Implement Task API",
            },
            headers=get_auth_headers(),
        )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "User Story not found."

@pytest.mark.parametrize(
    "http_method",
    ["GET", "POST"],
)
def test_task_api_without_story_id(http_method: str):
    """Verify that story_id is required for task operations."""
    if http_method == "GET":
        response = client.get(
            "/api/v1/tasks",
            headers=get_auth_headers(),
        )
    else:
        response = client.post(
            "/api/v1/tasks",
            json={
                "title": "Task Without User Story",
                "description": "This task has no story reference.",
            },
            headers=get_auth_headers(),
        )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    errors = response.json()["detail"]

    # Verify that the missing story_id caused the validation error.
    assert any(
        "story_id" in error["loc"]
        for error in errors
    )

@pytest.mark.parametrize(
    "pagination_params",
    [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
    ],
)
def test_list_tasks_with_invalid_pagination(pagination_params: dict):
    """Verify that invalid task pagination parameters are rejected."""
    from uuid import uuid4

    response = client.get(
        "/api/v1/tasks",
        params={
            "story_id": str(uuid4()),
            **pagination_params,
        },
        headers=get_auth_headers(),
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert response.json()["detail"]
