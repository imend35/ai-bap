
"""I test the JWT-protected human review and approval workflow."""

from contextlib import contextmanager
from uuid import uuid4

from fastapi import status
from fastapi.testclient import TestClient

from app.database import SessionLocal
from app.jwt_service import create_access_token
from app.main import app
from app.models import Project, Requirement, UserStory
from app.models.user import User

client = TestClient(app)


def get_jwt_headers(user_id) -> dict[str, str]:
    """I sign a real JWT for my authorized test user."""
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


@contextmanager
def prepare_story(
    initial_status: str = "draft",
    role: str | None = None,
):
    """I create and clean up records for my approval workflow tests."""

    # I create a project, requirement, and user story in PostgreSQL.
    with SessionLocal() as db:
        project = Project(
            name=f"AI BAP Approval Test {uuid4().hex}",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="Secure Account Management",
            description="Users must manage their accounts securely.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.flush()

        story = UserStory(
            requirement_id=requirement.id,
            title="Manage My Account",
            description=(
                "As a user, I want to manage my account "
                "so that my information remains accurate."
            ),
            acceptance_criteria=[
                "Given valid details, my changes are saved."
            ],
            status=initial_status,
        )
        db.add(story)

        user = None

        # I create a real database user when JWT authorization is needed.
        if role is not None:
            user = User(
                email=f"approval-{uuid4().hex}@example.com",
                full_name="Approval Test User",
                password_hash="test-only-not-for-login",
                role=role,
                is_active=True,
            )
            db.add(user)

        db.commit()

        project_id = project.id
        requirement_id = requirement.id
        story_id = story.id
        user_id = user.id if user is not None else None

    try:
        # I provide the identifiers needed by each test.
        yield project_id, requirement_id, story_id, user_id

    finally:
        # I remove temporary records after every test.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)

            if user_id is not None:
                user = db.get(User, user_id)

                if user is not None:
                    db.delete(user)

            db.commit()


@contextmanager
def prepare_editor():
    """I create a temporary business analyst for editing operations."""

    with SessionLocal() as db:
        editor = User(
            email=f"approval-editor-{uuid4().hex}@example.com",
            full_name="Approval Test Business Analyst",
            password_hash="test-only-not-for-login",
            role="business_analyst",
            is_active=True,
        )
        db.add(editor)
        db.commit()
        editor_id = editor.id

    try:
        yield editor_id
    finally:
        with SessionLocal() as db:
            editor = db.get(User, editor_id)
            if editor is not None:
                db.delete(editor)
                db.commit()


def test_draft_user_story_cannot_be_approved_directly():
    """I verify that a draft cannot bypass human review."""

    with prepare_story(role="admin") as (
        _project_id, _requirement_id, story_id, user_id
    ):
        # I attempt approval through the protected JWT endpoint.
        response = client.post(
            f"/api/v1/user-stories/{story_id}/approve",
            headers=get_jwt_headers(user_id),
        )

        assert response.status_code == status.HTTP_409_CONFLICT

        # I verify that the invalid approval did not change PostgreSQL.
        with SessionLocal() as db:
            saved_story = db.get(UserStory, story_id)
            assert saved_story is not None
            assert saved_story.status == "draft"


def test_user_story_can_be_approved_after_review():
    """I verify that an administrator can approve a reviewed story."""

    with prepare_story(role="admin") as (
        _project_id, _requirement_id, story_id, user_id
    ):
        # I submit my draft story for review with my administrator JWT.
        review_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "in_review"},
            headers=get_jwt_headers(user_id),
        )

        assert review_response.status_code == status.HTTP_200_OK
        assert review_response.json()["status"] == "in_review"

        # I approve the story using my administrator JWT.
        approval_response = client.post(
            f"/api/v1/user-stories/{story_id}/approve",
            headers=get_jwt_headers(user_id),
        )

        assert approval_response.status_code == status.HTTP_200_OK
        assert approval_response.json()["status"] == "approved"

        # I verify that PostgreSQL persisted my approval.
        with SessionLocal() as db:
            saved_story = db.get(UserStory, story_id)
            assert saved_story is not None
            assert saved_story.status == "approved"


def test_user_story_can_be_rejected_after_review():
    """I verify that a reviewer can reject a reviewed story."""

    with prepare_story(role="reviewer") as (
        _project_id, _requirement_id, story_id, user_id
    ), prepare_editor() as editor_id:
        # I use a business analyst to submit the story for review.
        review_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "in_review"},
            headers=get_jwt_headers(editor_id),
        )

        assert review_response.status_code == status.HTTP_200_OK
        assert review_response.json()["status"] == "in_review"

        # I reject the reviewed story using my reviewer JWT.
        rejection_response = client.post(
            f"/api/v1/user-stories/{story_id}/reject",
            headers=get_jwt_headers(user_id),
        )

        assert rejection_response.status_code == status.HTTP_200_OK
        assert rejection_response.json()["status"] == "rejected"

        # I verify that PostgreSQL persisted my rejection.
        with SessionLocal() as db:
            saved_story = db.get(UserStory, story_id)
            assert saved_story is not None
            assert saved_story.status == "rejected"


def test_rejected_user_story_can_be_revised_and_resubmitted():
    """I verify that I can revise and resubmit a rejected story."""

    with prepare_story(initial_status="rejected", role="business_analyst") as (
        _project_id, _requirement_id, story_id, user_id
    ):
        headers = get_jwt_headers(user_id)

        # I return my rejected story to draft status.
        draft_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "draft"},
            headers=headers,
        )

        assert draft_response.status_code == status.HTTP_200_OK
        assert draft_response.json()["status"] == "draft"

        # I improve the story description and acceptance criteria.
        revised_description = (
            "As a registered user, I want to update my account "
            "so that my personal information remains accurate."
        )
        revised_criteria = [
            "Given valid account details, changes are saved.",
            "Given invalid details, a validation error is displayed.",
        ]

        revision_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={
                "description": revised_description,
                "acceptance_criteria": revised_criteria,
            },
            headers=headers,
        )

        assert revision_response.status_code == status.HTTP_200_OK
        assert revision_response.json()["description"] == revised_description
        assert revision_response.json()["acceptance_criteria"] == revised_criteria

        # I resubmit my revised story for human review.
        review_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "in_review"},
            headers=headers,
        )

        assert review_response.status_code == status.HTTP_200_OK
        assert review_response.json()["status"] == "in_review"

        # I verify that all changes were saved.
        with SessionLocal() as db:
            saved_story = db.get(UserStory, story_id)
            assert saved_story is not None
            assert saved_story.status == "in_review"
            assert saved_story.description == revised_description
            assert saved_story.acceptance_criteria == revised_criteria


def test_approved_user_story_cannot_be_modified():
    """I verify that approved stories remain protected from changes."""

    with prepare_story(initial_status="approved", role="admin") as (
        _project_id, _requirement_id, story_id, user_id
    ):
        headers = get_jwt_headers(user_id)

        # I read the original approved story before attempting changes.
        with SessionLocal() as db:
            story = db.get(UserStory, story_id)
            assert story is not None
            original_title = story.title
            original_description = story.description
            original_criteria = list(story.acceptance_criteria)

        # I attempt to modify the approved story's content.
        content_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={
                "title": "Modified Account Story",
                "description": "This content should not be saved.",
                "acceptance_criteria": [
                    "This criterion should not be saved."
                ],
            },
            headers=headers,
        )

        assert content_response.status_code == status.HTTP_409_CONFLICT

        # I attempt to change the approved story's status.
        status_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "draft"},
            headers=headers,
        )

        assert status_response.status_code == status.HTTP_409_CONFLICT

        # I verify that PostgreSQL still contains the original values.
        with SessionLocal() as db:
            saved_story = db.get(UserStory, story_id)
            assert saved_story is not None
            assert saved_story.status == "approved"
            assert saved_story.title == original_title
            assert saved_story.description == original_description
            assert saved_story.acceptance_criteria == original_criteria


def test_user_story_cannot_be_created_as_approved():
    """I verify that story creation cannot bypass human approval."""

    with prepare_story(role="business_analyst") as (
        _project_id, requirement_id, _story_id, user_id
    ):
        # I count existing stories before attempting invalid creation.
        with SessionLocal() as db:
            initial_count = (
                db.query(UserStory)
                .filter(UserStory.requirement_id == requirement_id)
                .count()
            )

        # I attempt to create a story directly in approved status.
        response = client.post(
            "/api/v1/user-stories",
            json={
                "requirement_id": str(requirement_id),
                "title": "Register Securely",
                "description": (
                    "As a user, I want to register securely "
                    "so that I can create my account."
                ),
                "acceptance_criteria": [
                    "Given valid details, registration succeeds."
                ],
                "status": "approved",
            },
            headers=get_jwt_headers(user_id),
        )

        assert response.status_code == status.HTTP_409_CONFLICT

        # I verify that no additional story was created.
        with SessionLocal() as db:
            final_count = (
                db.query(UserStory)
                .filter(UserStory.requirement_id == requirement_id)
                .count()
            )

        assert final_count == initial_count
