
"""I test project API operations and role-based authorization."""

from contextlib import contextmanager
from datetime import date, datetime, timezone
from uuid import UUID, uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app
from app.models import Project, Requirement, Sprint, Task, UserStory
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


def test_get_project_dashboard_aggregates_project_scoped_records():
    """I return stored-record dashboard counts without including another project."""
    with temporary_project("Dashboard Project", "Dashboard target") as project_id:
        with temporary_project("Other Project", "Dashboard isolation") as other_project_id:
            with SessionLocal() as db:
                requirement = Requirement(
                    project_id=project_id,
                    title="Dashboard requirement",
                    description="Target project requirement",
                )
                second_requirement = Requirement(
                    project_id=project_id,
                    title="Second dashboard requirement",
                    description="Second target requirement",
                )
                other_requirement = Requirement(
                    project_id=other_project_id,
                    title="Other project requirement",
                    description="Must not affect target totals",
                )
                db.add_all([requirement, second_requirement, other_requirement])
                db.flush()

                approved_story = UserStory(
                    requirement_id=requirement.id,
                    title="Approved story",
                    description="Counts as approved",
                    acceptance_criteria=[],
                    status="approved",
                )
                draft_story = UserStory(
                    requirement_id=second_requirement.id,
                    title="Draft story",
                    description="Does not count as approved",
                    acceptance_criteria=[],
                    status="draft",
                )
                other_story = UserStory(
                    requirement_id=other_requirement.id,
                    title="Other approved story",
                    description="Must not affect target counts",
                    acceptance_criteria=[],
                    status="approved",
                )
                db.add_all([approved_story, draft_story, other_story])
                db.flush()

                todo_task = Task(
                    story_id=approved_story.id,
                    title="To do task",
                    status="todo",
                )
                db.add_all(
                    [
                        todo_task,
                        Task(
                            story_id=approved_story.id,
                            title="In progress task",
                            status="in_progress",
                        ),
                        Task(
                            story_id=draft_story.id,
                            title="In review task",
                            status="in_review",
                        ),
                        Task(
                            story_id=draft_story.id,
                            title="Done task",
                            status="done",
                        ),
                        Task(
                            story_id=other_story.id,
                            title="Other project task",
                            status="done",
                        ),
                        Sprint(
                            project_id=project_id,
                            name="Active sprint",
                            start_date=date(2026, 1, 1),
                            end_date=date(2026, 1, 14),
                            status="active",
                        ),
                        Sprint(
                            project_id=project_id,
                            name="Completed sprint",
                            start_date=date(2025, 12, 1),
                            end_date=date(2025, 12, 14),
                            status="completed",
                        ),
                        Sprint(
                            project_id=other_project_id,
                            name="Other active sprint",
                            start_date=date(2026, 1, 1),
                            end_date=date(2026, 1, 14),
                            status="active",
                        ),
                    ]
                )
                db.commit()

            with authenticated_as() as api:
                response = api.get(f"{BASE_URL}/{project_id}/dashboard")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert set(data) == {
                "project_id",
                "total_requirements",
                "approved_user_stories",
                "tasks_by_status",
                "active_sprints",
            }
            assert data["project_id"] == str(project_id)
            assert data["total_requirements"] == 2
            assert data["approved_user_stories"] == 1
            assert data["tasks_by_status"] == {
                "todo": 1,
                "in_progress": 1,
                "in_review": 1,
                "done": 1,
            }
            assert data["active_sprints"] == 1
            assert all(
                isinstance(value, int)
                for value in (
                    data["total_requirements"],
                    data["approved_user_stories"],
                    data["active_sprints"],
                    *data["tasks_by_status"].values(),
                )
            )

            with SessionLocal() as db:
                persisted_task = db.get(Task, todo_task.id)
                assert persisted_task is not None
                persisted_task.status = "done"
                db.commit()

            with authenticated_as() as api:
                transitioned_response = api.get(f"{BASE_URL}/{project_id}/dashboard")

            assert transitioned_response.status_code == status.HTTP_200_OK
            assert transitioned_response.json()["tasks_by_status"] == {
                "todo": 0,
                "in_progress": 1,
                "in_review": 1,
                "done": 2,
            }


def test_get_project_dashboard_returns_zero_counts_for_empty_project():
    """I return every task-status key with zero counts for an empty project."""
    with temporary_project("Empty Dashboard Project", "No related records") as project_id:
        with authenticated_as() as api:
            response = api.get(f"{BASE_URL}/{project_id}/dashboard")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "project_id": str(project_id),
        "total_requirements": 0,
        "approved_user_stories": 0,
        "tasks_by_status": {
            "todo": 0,
            "in_progress": 0,
            "in_review": 0,
            "done": 0,
        },
        "active_sprints": 0,
    }


def test_get_project_dashboard_for_unknown_project():
    """I retain the established project-not-found dashboard response."""
    with authenticated_as() as api:
        response = api.get(f"{BASE_URL}/{uuid4()}/dashboard")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Project not found."


def test_get_project_dashboard_without_token():
    """I require authentication for dashboard reads."""
    response = client.get(f"{BASE_URL}/{uuid4()}/dashboard")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("role", [ADMIN, BUSINESS_ANALYST, REVIEWER])
def test_all_roles_can_get_project_dashboard(role):
    """I allow every supported role to read a project dashboard."""
    with temporary_project("Dashboard Role Test", "Role access") as project_id:
        with authenticated_as(role) as api:
            response = api.get(f"{BASE_URL}/{project_id}/dashboard")

    assert response.status_code == status.HTTP_200_OK


def test_get_project_traceability_returns_complete_project_scoped_hierarchy():
    """I return persisted Requirement, Story, and Task links without leakage."""
    with temporary_project("Traceability Project", "Traceability target") as project_id:
        with temporary_project("Other Project", "Traceability isolation") as other_project_id:
            with SessionLocal() as db:
                requirement_with_stories = Requirement(
                    id=UUID("00000000-0000-0000-0000-000000000003"),
                    project_id=project_id,
                    title="Requirement with stories",
                    description="I have linked stories.",
                    priority="high",
                    status="approved",
                    created_at=datetime(2026, 3, 3, tzinfo=timezone.utc),
                )
                requirement_without_stories = Requirement(
                    id=UUID("00000000-0000-0000-0000-000000000002"),
                    project_id=project_id,
                    title="Requirement without stories",
                    description="I remain visible without children.",
                    priority="low",
                    status="draft",
                    created_at=datetime(2026, 3, 2, tzinfo=timezone.utc),
                )
                other_requirement = Requirement(
                    project_id=other_project_id,
                    title="Other project requirement",
                    description="I must not appear.",
                    priority="critical",
                    status="approved",
                )
                db.add_all(
                    [
                        requirement_with_stories,
                        requirement_without_stories,
                        other_requirement,
                    ]
                )
                db.flush()

                draft_story = UserStory(
                    id=UUID("00000000-0000-0000-0000-000000000011"),
                    requirement_id=requirement_with_stories.id,
                    title="Draft story",
                    description="I remain included.",
                    acceptance_criteria=[],
                    status="draft",
                    created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
                )
                approved_story = UserStory(
                    id=UUID("00000000-0000-0000-0000-000000000013"),
                    requirement_id=requirement_with_stories.id,
                    title="Approved story",
                    description="I include every task status.",
                    acceptance_criteria=[],
                    status="approved",
                    created_at=datetime(2026, 3, 3, tzinfo=timezone.utc),
                )
                rejected_story_without_tasks = UserStory(
                    id=UUID("00000000-0000-0000-0000-000000000012"),
                    requirement_id=requirement_with_stories.id,
                    title="Rejected story without tasks",
                    description="I remain included without tasks.",
                    acceptance_criteria=[],
                    status="rejected",
                    created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
                )
                other_story = UserStory(
                    requirement_id=other_requirement.id,
                    title="Other project story",
                    description="I must not appear.",
                    acceptance_criteria=[],
                    status="approved",
                )
                db.add_all(
                    [
                        draft_story,
                        approved_story,
                        rejected_story_without_tasks,
                        other_story,
                    ]
                )
                db.flush()

                db.add_all(
                    [
                        Task(
                            id=UUID("00000000-0000-0000-0000-000000000021"),
                            story_id=draft_story.id,
                            title="Draft story task",
                            status="todo",
                            created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
                        ),
                        Task(
                            id=UUID("00000000-0000-0000-0000-000000000022"),
                            story_id=approved_story.id,
                            title="In progress task",
                            status="in_progress",
                            created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
                        ),
                        Task(
                            id=UUID("00000000-0000-0000-0000-000000000024"),
                            story_id=approved_story.id,
                            title="In review task",
                            status="in_review",
                            created_at=datetime(2026, 3, 3, tzinfo=timezone.utc),
                        ),
                        Task(
                            id=UUID("00000000-0000-0000-0000-000000000025"),
                            story_id=approved_story.id,
                            title="To do tied task",
                            status="todo",
                            created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
                        ),
                        Task(
                            id=UUID("00000000-0000-0000-0000-000000000023"),
                            story_id=approved_story.id,
                            title="Done task",
                            status="done",
                            created_at=datetime(2026, 3, 2, tzinfo=timezone.utc),
                        ),
                        Task(
                            story_id=other_story.id,
                            title="Other project task",
                            status="done",
                        ),
                    ]
                )
                db.commit()

            with authenticated_as() as api:
                response = api.get(f"{BASE_URL}/{project_id}/traceability")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert set(data) == {"items", "total", "limit", "offset"}
            assert data["total"] == 2
            assert data["limit"] == 20
            assert data["offset"] == 0
            assert [requirement["id"] for requirement in data["items"]] == [
                str(requirement_with_stories.id),
                str(requirement_without_stories.id),
            ]

            requirements_by_title = {
                requirement["title"]: requirement for requirement in data["items"]
            }
            assert set(requirements_by_title) == {
                "Requirement with stories",
                "Requirement without stories",
            }
            assert requirements_by_title["Requirement without stories"]["stories"] == []

            traced_requirement = requirements_by_title["Requirement with stories"]
            assert traced_requirement["id"] == str(requirement_with_stories.id)
            assert traced_requirement["record_number"].startswith("REQ-")
            assert traced_requirement["status"] == "approved"
            assert traced_requirement["priority"] == "high"

            stories_by_title = {
                story["title"]: story for story in traced_requirement["stories"]
            }
            assert set(stories_by_title) == {
                "Draft story",
                "Approved story",
                "Rejected story without tasks",
            }
            assert stories_by_title["Draft story"]["status"] == "draft"
            assert stories_by_title["Approved story"]["status"] == "approved"
            assert stories_by_title["Rejected story without tasks"]["status"] == "rejected"
            assert stories_by_title["Rejected story without tasks"]["tasks"] == []
            assert [story["id"] for story in traced_requirement["stories"]] == [
                str(approved_story.id),
                str(rejected_story_without_tasks.id),
                str(draft_story.id),
            ]
            assert all(
                story["record_number"].startswith("US-")
                for story in stories_by_title.values()
            )

            assert stories_by_title["Draft story"]["tasks"] == [
                {
                    "id": str(UUID("00000000-0000-0000-0000-000000000021")),
                    "title": "Draft story task",
                    "status": "todo",
                }
            ]
            assert stories_by_title["Approved story"]["tasks"] == [
                {
                    "id": str(UUID("00000000-0000-0000-0000-000000000024")),
                    "title": "In review task",
                    "status": "in_review",
                },
                {
                    "id": str(UUID("00000000-0000-0000-0000-000000000023")),
                    "title": "Done task",
                    "status": "done",
                },
                {
                    "id": str(UUID("00000000-0000-0000-0000-000000000025")),
                    "title": "To do tied task",
                    "status": "todo",
                },
                {
                    "id": str(UUID("00000000-0000-0000-0000-000000000022")),
                    "title": "In progress task",
                    "status": "in_progress",
                },
            ]


def test_get_project_traceability_paginates_roots_and_handles_empty_results():
    """I paginate only root Requirements and retain the requested offset."""
    with temporary_project("Traceability Pages", "Pagination target") as project_id:
        with SessionLocal() as db:
            older_tied_requirement = Requirement(
                id=UUID("00000000-0000-0000-0000-000000000101"),
                project_id=project_id,
                title="Older tied requirement",
                description="I test the ID tie-breaker.",
                created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
            )
            newer_tied_requirement = Requirement(
                id=UUID("00000000-0000-0000-0000-000000000102"),
                project_id=project_id,
                title="Newer tied requirement",
                description="I win the ID tie-breaker.",
                created_at=datetime(2026, 4, 1, tzinfo=timezone.utc),
            )
            latest_requirement = Requirement(
                id=UUID("00000000-0000-0000-0000-000000000103"),
                project_id=project_id,
                title="Latest requirement",
                description="I win on created_at.",
                created_at=datetime(2026, 4, 2, tzinfo=timezone.utc),
            )
            db.add_all(
                [
                    older_tied_requirement,
                    newer_tied_requirement,
                    latest_requirement,
                ]
            )
            db.commit()

        with authenticated_as() as api:
            first_page = api.get(
                f"{BASE_URL}/{project_id}/traceability?limit=1&offset=0"
            )
            second_page = api.get(
                f"{BASE_URL}/{project_id}/traceability?limit=1&offset=1"
            )
            ordered_page = api.get(
                f"{BASE_URL}/{project_id}/traceability?limit=3&offset=0"
            )
            out_of_range = api.get(
                f"{BASE_URL}/{project_id}/traceability?limit=1&offset=3"
            )

        assert first_page.status_code == status.HTTP_200_OK
        assert second_page.status_code == status.HTTP_200_OK
        assert out_of_range.status_code == status.HTTP_200_OK
        assert first_page.json()["total"] == 3
        assert first_page.json()["limit"] == 1
        assert first_page.json()["offset"] == 0
        assert second_page.json()["total"] == 3
        assert second_page.json()["offset"] == 1
        assert len(first_page.json()["items"]) == 1
        assert len(second_page.json()["items"]) == 1
        assert first_page.json()["items"][0]["id"] == str(latest_requirement.id)
        assert second_page.json()["items"][0]["id"] == str(newer_tied_requirement.id)
        assert [item["id"] for item in ordered_page.json()["items"]] == [
            str(latest_requirement.id),
            str(newer_tied_requirement.id),
            str(older_tied_requirement.id),
        ]
        assert out_of_range.json() == {
            "items": [],
            "total": 3,
            "limit": 1,
            "offset": 3,
        }


def test_get_project_traceability_returns_empty_page_for_empty_project():
    """I return an empty root collection for an existing project without requirements."""
    with temporary_project("Empty Traceability", "No requirements") as project_id:
        with authenticated_as() as api:
            response = api.get(f"{BASE_URL}/{project_id}/traceability")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "items": [],
        "total": 0,
        "limit": 20,
        "offset": 0,
    }


def test_get_project_traceability_does_not_mutate_persisted_records():
    """I keep traceability reads free of persisted data changes."""
    with temporary_project("Read-only Traceability", "No writes") as project_id:
        with SessionLocal() as db:
            requirement = Requirement(
                project_id=project_id,
                title="Read-only requirement",
                description="I remain unchanged after a GET.",
            )
            db.add(requirement)
            db.commit()
            requirement_id = requirement.id

        with authenticated_as() as api:
            response = api.get(f"{BASE_URL}/{project_id}/traceability")

        assert response.status_code == status.HTTP_200_OK
        with SessionLocal() as db:
            persisted_requirement = db.get(Requirement, requirement_id)
            assert persisted_requirement is not None
            assert persisted_requirement.title == "Read-only requirement"


def test_get_project_traceability_rejects_unknown_or_invalid_requests():
    """I preserve project-read errors and pagination validation semantics."""
    with authenticated_as() as api:
        unknown_project = api.get(f"{BASE_URL}/{uuid4()}/traceability")
        invalid_uuid = api.get(f"{BASE_URL}/invalid-uuid/traceability")
        invalid_limit = api.get(f"{BASE_URL}/{uuid4()}/traceability?limit=0")
        invalid_offset = api.get(f"{BASE_URL}/{uuid4()}/traceability?offset=-1")

    assert unknown_project.status_code == status.HTTP_404_NOT_FOUND
    assert unknown_project.json()["detail"] == "Project not found."
    assert invalid_uuid.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert invalid_limit.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT
    assert invalid_offset.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_get_project_traceability_without_token():
    """I require authentication for traceability reads."""
    response = client.get(f"{BASE_URL}/{uuid4()}/traceability")

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize("role", [ADMIN, BUSINESS_ANALYST, REVIEWER])
def test_all_roles_can_get_project_traceability(role):
    """I allow every supported role to read project traceability."""
    with temporary_project("Traceability Role Test", "Role access") as project_id:
        with authenticated_as(role) as api:
            response = api.get(f"{BASE_URL}/{project_id}/traceability")

    assert response.status_code == status.HTTP_200_OK


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
