
"""I verify audit identity snapshots for approval decisions."""

from uuid import uuid4

from sqlalchemy import select

from app.database import SessionLocal
from app.models import UserStoryApprovalAudit
from app.models.user import User
from tests.test_user_story_approval_api import (
    client,
    get_jwt_headers,
    prepare_editor,
    prepare_story,
)


def test_approval_persists_audit_identity_snapshots():
    """I verify that approval persists both original identifiers."""

    with prepare_story(role="admin") as (
        _project_id,
        _requirement_id,
        story_id,
        user_id,
    ):
        # I submit the story for review with an administrator JWT.
        review_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "in_review"},
            headers=get_jwt_headers(user_id),
        )
        assert review_response.status_code == 200

        # I approve the reviewed story with the same administrator.
        approval_response = client.post(
            f"/api/v1/user-stories/{story_id}/approve",
            headers=get_jwt_headers(user_id),
        )
        assert approval_response.status_code == 200

        # I verify the audit record preserves the original identities.
        with SessionLocal() as db:
            audit = db.scalar(
                select(UserStoryApprovalAudit)
                .where(
                    UserStoryApprovalAudit.user_story_id_snapshot == story_id
                )
                .where(
                    UserStoryApprovalAudit.actor_id_snapshot == user_id
                )
                .where(UserStoryApprovalAudit.action == "approved")
                .order_by(UserStoryApprovalAudit.created_at.desc())
            )

            assert audit is not None
            assert audit.user_story_id_snapshot == story_id
            assert audit.actor_id_snapshot == user_id
            assert audit.previous_status == "in_review"
            assert audit.new_status == "approved"


def test_rejection_persists_audit_identity_snapshots():
    """I verify that rejection persists both original identifiers."""

    with prepare_story(role="reviewer") as (
        _project_id,
        _requirement_id,
        story_id,
        user_id,
    ), prepare_editor() as editor_id:
        # I use a business analyst to submit the story for review.
        review_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "in_review"},
            headers=get_jwt_headers(editor_id),
        )
        assert review_response.status_code == 200

        # I reject the story using the reviewer's own JWT.
        rejection_response = client.post(
            f"/api/v1/user-stories/{story_id}/reject",
            headers=get_jwt_headers(user_id),
        )
        assert rejection_response.status_code == 200

        # I verify the reviewer identity was saved in the audit.
        with SessionLocal() as db:
            audit = db.scalar(
                select(UserStoryApprovalAudit)
                .where(
                    UserStoryApprovalAudit.user_story_id_snapshot == story_id
                )
                .where(
                    UserStoryApprovalAudit.actor_id_snapshot == user_id
                )
                .where(UserStoryApprovalAudit.action == "rejected")
                .order_by(UserStoryApprovalAudit.created_at.desc())
            )

            assert audit is not None
            assert audit.user_story_id_snapshot == story_id
            assert audit.actor_id_snapshot == user_id
            assert audit.previous_status == "in_review"
            assert audit.new_status == "rejected"


def test_audit_snapshots_survive_user_and_story_deletion():
    """I verify that audit identity snapshots survive record deletion."""

    with prepare_story(role="admin") as (
        _project_id,
        _requirement_id,
        story_id,
        user_id,
    ):
        # I submit the story for review using a real JWT.
        review_response = client.patch(
            f"/api/v1/user-stories/{story_id}",
            json={"status": "in_review"},
            headers=get_jwt_headers(user_id),
        )
        assert review_response.status_code == 200

        # I approve the story and create its audit record.
        approval_response = client.post(
            f"/api/v1/user-stories/{story_id}/approve",
            headers=get_jwt_headers(user_id),
        )
        assert approval_response.status_code == 200

        # I record the audit ID before temporary records are deleted.
        with SessionLocal() as db:
            audit = db.scalar(
                select(UserStoryApprovalAudit)
                .where(
                    UserStoryApprovalAudit.user_story_id_snapshot == story_id
                )
                .where(
                    UserStoryApprovalAudit.actor_id_snapshot == user_id
                )
                .where(UserStoryApprovalAudit.action == "approved")
                .order_by(UserStoryApprovalAudit.created_at.desc())
            )

            assert audit is not None
            audit_id = audit.id

    # I verify that identity snapshots survive cleanup of related records.
    with SessionLocal() as db:
        saved_audit = db.get(UserStoryApprovalAudit, audit_id)

        assert saved_audit is not None
        assert saved_audit.user_story_id is None
        assert saved_audit.actor_id is None
        assert saved_audit.user_story_id_snapshot == story_id
        assert saved_audit.actor_id_snapshot == user_id


def test_admin_can_access_audit_history():
    """I verify that an administrator can read audit history."""

    with prepare_story(role="admin") as (
        _project_id,
        _requirement_id,
        story_id,
        user_id,
    ):
        response = client.get(
            f"/api/v1/user-stories/{story_id}/audit",
            headers=get_jwt_headers(user_id),
        )

        assert response.status_code == 200
        assert "items" in response.json()
        assert response.json()["total"] == len(response.json()["items"])


def test_business_analyst_cannot_access_audit_history():
    """I verify that business analysts cannot read audit history."""

    with prepare_story(role="business_analyst") as (
        _project_id,
        _requirement_id,
        story_id,
        user_id,
    ):
        response = client.get(
            f"/api/v1/user-stories/{story_id}/audit",
            headers=get_jwt_headers(user_id),
        )

        assert response.status_code == 403


def test_reviewer_can_access_audit_history():
    """I verify that reviewers can read audit history."""

    with prepare_story(role="reviewer") as (
        _project_id,
        _requirement_id,
        story_id,
        user_id,
    ):
        response = client.get(
            f"/api/v1/user-stories/{story_id}/audit",
            headers=get_jwt_headers(user_id),
        )

        assert response.status_code == 200
        assert response.json()["total"] == len(response.json()["items"])


def test_audit_history_rejects_missing_jwt():
    """I verify that audit history requires authentication."""

    with prepare_story() as (
        _project_id,
        _requirement_id,
        story_id,
        _user_id,
    ):
        response = client.get(
            f"/api/v1/user-stories/{story_id}/audit",
        )

        assert response.status_code == 401


def test_audit_history_survives_story_and_actor_deletion():
    """I verify that audit history remains accessible after deletion."""

    # I create a separate administrator to read the audit history.
    with SessionLocal() as db:
        audit_reader = User(
            email=f"audit-reader-{uuid4().hex}@example.com",
            full_name="Audit History Reader",
            password_hash="test-only-not-for-login",
            role="admin",
            is_active=True,
        )
        db.add(audit_reader)
        db.commit()
        reader_id = audit_reader.id

    try:
        with prepare_story(role="reviewer") as (
            _project_id,
            _requirement_id,
            story_id,
            actor_id,
        ), prepare_editor() as editor_id:
            # I submit the story using a business analyst JWT.
            review_response = client.patch(
                f"/api/v1/user-stories/{story_id}",
                json={"status": "in_review"},
                headers=get_jwt_headers(editor_id),
            )
            assert review_response.status_code == 200

            # I approve the story using the reviewer's JWT.
            approval_response = client.post(
                f"/api/v1/user-stories/{story_id}/approve",
                headers=get_jwt_headers(actor_id),
            )
            assert approval_response.status_code == 200

        # I read the audit history after the story and actor are deleted.
        response = client.get(
            f"/api/v1/user-stories/{story_id}/audit",
            headers=get_jwt_headers(reader_id),
        )

        assert response.status_code == 200

        payload = response.json()
        assert payload["total"] >= 1

        matching_records = [
            item
            for item in payload["items"]
            if item["user_story_id_snapshot"] == str(story_id)
            and item["actor_id_snapshot"] == str(actor_id)
            and item["action"] == "approved"
        ]

        assert matching_records, (
            "I expected the deleted story's approval audit to remain accessible."
        )

        # I verify that deleted foreign keys do not erase the snapshots.
        audit = matching_records[0]
        assert audit["user_story_id"] is None
        assert audit["actor_id"] is None
        assert audit["user_story_id_snapshot"] == str(story_id)
        assert audit["actor_id_snapshot"] == str(actor_id)

    finally:
        # I remove the separate audit reader after the test.
        with SessionLocal() as db:
            reader = db.get(User, reader_id)
            if reader is not None:
                db.delete(reader)
                db.commit()
