
"""I test the human review and approval workflow for user stories."""

from fastapi import status
from fastapi.testclient import TestClient

from app.config import get_settings
from app.database import SessionLocal
from app.main import app
from app.models import Project, Requirement, UserStory


client = TestClient(app)


def get_auth_headers() -> dict[str, str]:
    """I prepare valid authentication headers for my API tests."""
    token = get_settings().demo_access_token.get_secret_value()
    return {"Authorization": f"Bearer {token}"}


def test_draft_user_story_cannot_be_approved_directly():
    """I verify that a draft cannot be approved without review."""

    # I create temporary project and requirement records.
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Approval Workflow Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="Secure User Login",
            description="Users must log in securely.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.flush()

        # I create a user story with an initial draft status.
        story = UserStory(
            requirement_id=requirement.id,
            title="Login with Email",
            description=(
                "As a user, I want to log in with my email "
                "so that I can access my account."
            ),
            acceptance_criteria=[
                "Given valid credentials, login succeeds."
            ],
            status="draft",
        )
        db.add(story)
        db.commit()

        project_id = project.id
        story_id = story.id

    try:
        # I attempt to approve the story without a review step.
        response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "approved"},
            headers=get_auth_headers(),
        )

        # I expect the API to reject the invalid transition.
        assert response.status_code == status.HTTP_409_CONFLICT

        # I verify that the rejected request does not change the database.
        with SessionLocal() as db:
            saved_story = db.get(UserStory, story_id)

            assert saved_story is not None
            assert saved_story.status == "draft"

    finally:
        # I remove my temporary test records.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()


def test_user_story_can_be_approved_after_review():
    """I verify that a reviewed user story can be approved."""

    # I create a temporary project for my approval test.
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Human Approval Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="Password Reset",
            description="Users must be able to reset passwords.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.flush()

        # I create a user story in draft status.
        story = UserStory(
            requirement_id=requirement.id,
            title="Reset Forgotten Password",
            description=(
                "As a user, I want to reset my password "
                "so that I can regain access to my account."
            ),
            acceptance_criteria=[
                "Given a valid email, a reset link is sent."
            ],
            status="draft",
        )
        db.add(story)
        db.commit()

        project_id = project.id
        story_id = story.id

    try:
        # I submit the draft user story for human review.
        review_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "in_review"},
            headers=get_auth_headers(),
        )

        assert review_response.status_code == status.HTTP_200_OK
        assert review_response.json()["status"] == "in_review"

        # I approve the user story after the review stage.
        approval_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "approved"},
            headers=get_auth_headers(),
        )

        assert approval_response.status_code == status.HTTP_200_OK
        assert approval_response.json()["status"] == "approved"

        # I verify that the approval is persisted in PostgreSQL.
        with SessionLocal() as db:
            saved_story = db.get(UserStory, story_id)

            assert saved_story is not None
            assert saved_story.status == "approved"

    finally:
        # I clean up my temporary database records.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()


def test_user_story_can_be_rejected_after_review():
    """I verify that a reviewed user story can be rejected."""

    # I create a temporary project and requirement.
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Human Rejection Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="Email Notifications",
            description="Users must receive email notifications.",
            priority="medium",
            status="draft",
        )
        db.add(requirement)
        db.flush()

        # I create a draft user story for my rejection scenario.
        story = UserStory(
            requirement_id=requirement.id,
            title="Receive Email Notifications",
            description=(
                "As a user, I want to receive email notifications "
                "so that I can stay informed."
            ),
            acceptance_criteria=[
                "Given an important event, an email is sent."
            ],
            status="draft",
        )
        db.add(story)
        db.commit()

        project_id = project.id
        story_id = story.id

    try:
        # I move the story to the review stage.
        review_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "in_review"},
            headers=get_auth_headers(),
        )

        assert review_response.status_code == status.HTTP_200_OK
        assert review_response.json()["status"] == "in_review"

        # I reject the user story after reviewing it.
        rejection_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "rejected"},
            headers=get_auth_headers(),
        )

        assert rejection_response.status_code == status.HTTP_200_OK
        assert rejection_response.json()["status"] == "rejected"

        # I verify that PostgreSQL stores the rejection status.
        with SessionLocal() as db:
            saved_story = db.get(UserStory, story_id)

            assert saved_story is not None
            assert saved_story.status == "rejected"

    finally:
        # I remove the temporary records created by this test.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()


def test_rejected_user_story_can_be_revised_and_resubmitted():
    """I verify that I can revise and resubmit a rejected story."""

    # I prepare temporary records for the revision workflow.
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Revision Workflow Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="Profile Management",
            description="Users must be able to manage their profiles.",
            priority="medium",
            status="draft",
        )
        db.add(requirement)
        db.flush()

        # I prepare a user story that was previously rejected.
        story = UserStory(
            requirement_id=requirement.id,
            title="Update User Profile",
            description="As a user, I want to update my profile.",
            acceptance_criteria=[
                "Given a profile update, the changes are saved."
            ],
            status="rejected",
        )
        db.add(story)
        db.commit()

        project_id = project.id
        story_id = story.id

    try:
        # I return the rejected story to draft status.
        draft_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "draft"},
            headers=get_auth_headers(),
        )

        assert draft_response.status_code == status.HTTP_200_OK
        assert draft_response.json()["status"] == "draft"

        # I improve the description and acceptance criteria.
        revised_description = (
            "As a registered user, I want to update my profile "
            "so that my personal information remains accurate."
        )
        revised_criteria = [
            "Given valid profile details, changes are saved.",
            "Given invalid details, a validation error is displayed.",
        ]

        revision_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={
                "description": revised_description,
                "acceptance_criteria": revised_criteria,
            },
            headers=get_auth_headers(),
        )

        assert revision_response.status_code == status.HTTP_200_OK
        assert revision_response.json()["description"] == revised_description
        assert revision_response.json()["acceptance_criteria"] == revised_criteria

        # I resubmit the revised story for human review.
        review_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "in_review"},
            headers=get_auth_headers(),
        )

        assert review_response.status_code == status.HTTP_200_OK
        assert review_response.json()["status"] == "in_review"

        # I verify that all changes are persisted in PostgreSQL.
        with SessionLocal() as db:
            saved_story = db.get(UserStory, story_id)

            assert saved_story is not None
            assert saved_story.status == "in_review"
            assert saved_story.description == revised_description
            assert saved_story.acceptance_criteria == revised_criteria

    finally:
        # I clean up my temporary test data.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()


def test_approved_user_story_cannot_be_modified():
    """I verify that approved user stories remain protected from changes."""

    # I create a temporary project and requirement for this security test.
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Approved Story Protection Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="Secure Payments",
            description="Users must complete payments securely.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.flush()

        # I create an already approved story to test its protection.
        original_title = "Complete Secure Payment"
        original_description = (
            "As a user, I want to pay securely "
            "so that I can complete my purchase."
        )
        original_criteria = [
            "Given valid payment details, payment succeeds."
        ]

        story = UserStory(
            requirement_id=requirement.id,
            title=original_title,
            description=original_description,
            acceptance_criteria=original_criteria,
            status="approved",
        )
        db.add(story)
        db.commit()

        project_id = project.id
        story_id = story.id

    try:
        # I attempt to modify the approved story's content.
        content_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={
                "title": "Modified Payment Story",
                "description": "This content should not be saved.",
                "acceptance_criteria": [
                    "This criterion should not be saved."
                ],
            },
            headers=get_auth_headers(),
        )

        # I expect the API to reject modifications to approved content.
        assert content_response.status_code == status.HTTP_409_CONFLICT

        # I also attempt to change the approved story's status.
        status_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "draft"},
            headers=get_auth_headers(),
        )

        # I expect the approved status to remain protected.
        assert status_response.status_code == status.HTTP_409_CONFLICT

        # I verify that the original values remain unchanged in PostgreSQL.
        with SessionLocal() as db:
            saved_story = db.get(UserStory, story_id)

            assert saved_story is not None
            assert saved_story.status == "approved"
            assert saved_story.title == original_title
            assert saved_story.description == original_description
            assert saved_story.acceptance_criteria == original_criteria

    finally:
        # I remove the temporary test records.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()

def test_user_story_cannot_be_created_as_approved():
    """I verify that new user stories cannot bypass human review."""

    # I create a temporary project and requirement for my security test.
    with SessionLocal() as db:
        project = Project(
            name="AI BAP Direct Approval Creation Test",
            status="planned",
        )
        db.add(project)
        db.flush()

        requirement = Requirement(
            project_id=project.id,
            title="Secure Account Registration",
            description="Users must register securely.",
            priority="high",
            status="draft",
        )
        db.add(requirement)
        db.commit()

        project_id = project.id
        requirement_id = requirement.id

    try:
        # I attempt to create an already approved user story.
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
            headers=get_auth_headers(),
        )

        # I expect the API to reject direct approval during creation.
        assert response.status_code == status.HTTP_409_CONFLICT

        # I verify that the rejected story was not saved in PostgreSQL.
        with SessionLocal() as db:
            saved_stories = (
                db.query(UserStory)
                .filter(UserStory.requirement_id == requirement_id)
                .all()
            )

            assert saved_stories == []

    finally:
        # I remove the temporary records created by my test.
        with SessionLocal() as db:
            project = db.get(Project, project_id)

            if project is not None:
                db.delete(project)
                db.commit()
