"""I verify record identity and creator behavior against isolated PostgreSQL.

These integration tests are protected by tests/conftest.py. They must run only
with the explicit isolated PostgreSQL environment accepted by
app.test_database_safety; they never select a database target themselves.
"""

import re
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.jwt_service import create_access_token
from app.main import app
from app.models import (
    Project,
    Requirement,
    User,
    UserStory,
    UserStoryApprovalAudit,
)

PROJECTS_URL = "/api/v1/projects"
REQUIREMENTS_URL = "/api/v1/requirements"
STORIES_URL = "/api/v1/user-stories"


def headers_for(user_id: UUID) -> dict[str, str]:
    """I create a real JWT header for a persisted isolated-test user."""

    return {"Authorization": f"Bearer {create_access_token(user_id)}"}


def assert_record_number(value: str, prefix: str) -> None:
    """I verify a generated record number without assuming its sequence value."""

    assert re.fullmatch(rf"{prefix}-[0-9]{{3,}}", value)


@pytest.fixture
def client():
    """I provide a FastAPI client backed by the guarded test environment."""

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def persisted_user():
    """I create and clean up a real business analyst identity."""

    with SessionLocal() as db:
        user = User(
            email=f"identity-api-{uuid4().hex}@example.com",
            full_name="Record Identity Test User",
            password_hash="test-only-not-for-login",
            role="business_analyst",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        user_id = user.id
        record_number = user.record_number
        full_name = user.full_name

    try:
        yield {
            "id": user_id,
            "record_number": record_number,
            "full_name": full_name,
            "headers": headers_for(user_id),
        }
    finally:
        with SessionLocal() as db:
            user = db.get(User, user_id)
            if user is not None:
                db.delete(user)
                db.commit()


@pytest.fixture
def identity_graph(client, persisted_user):
    """I create API-owned project, requirement, and story records."""

    headers = persisted_user["headers"]
    project_response = client.post(
        PROJECTS_URL,
        headers=headers,
        json={
            "name": f"Identity Project {uuid4().hex}",
            "description": "A project created by the identity integration test.",
            "status": "planned",
        },
    )
    assert project_response.status_code == 201, project_response.text
    project = project_response.json()

    requirement_response = client.post(
        REQUIREMENTS_URL,
        headers=headers,
        json={
            "project_id": project["id"],
            "title": "Identity Requirement",
            "description": "A requirement created by the integration test.",
            "priority": "high",
            "status": "draft",
        },
    )
    assert requirement_response.status_code == 201, requirement_response.text
    requirement = requirement_response.json()

    story_response = client.post(
        STORIES_URL,
        headers=headers,
        json={
            "requirement_id": requirement["id"],
            "title": "Identity User Story",
            "description": "As a user, I need identity data in responses.",
            "acceptance_criteria": ["Given a new story, its creator is visible in the response."],
            "status": "draft",
        },
    )
    assert story_response.status_code == 201, story_response.text
    story = story_response.json()

    try:
        yield {
            "creator": persisted_user,
            "project": project,
            "requirement": requirement,
            "story": story,
        }
    finally:
        with SessionLocal() as db:
            project_record = db.get(Project, UUID(project["id"]))
            if project_record is not None:
                db.delete(project_record)
                db.commit()


def test_registration_and_me_return_immutable_usr_record_numbers(client):
    """I verify registration and profile responses expose the same USR number."""

    email = f"identity-registration-{uuid4().hex}@example.com"
    payload = {
        "email": email,
        "full_name": "Registration Identity User",
        "password": "TestPassword123!",
    }

    try:
        registration = client.post("/api/v1/auth/register", json=payload)
        assert registration.status_code == 201, registration.text
        registered = registration.json()
        assert_record_number(registered["record_number"], "USR")

        login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": payload["password"]},
        )
        assert login.status_code == 200, login.text
        profile = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )
        assert profile.status_code == 200, profile.text
        assert profile.json()["record_number"] == registered["record_number"]

        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email))
            assert user is not None
            assert user.record_number == registered["record_number"]
    finally:
        with SessionLocal() as db:
            user = db.scalar(select(User).where(User.email == email))
            if user is not None:
                db.delete(user)
                db.commit()


def test_creation_assigns_creator_and_returns_all_record_numbers(identity_graph):
    """I verify new API records retain the authenticated creator identity."""

    creator = identity_graph["creator"]
    expected_creator = {
        "record_number": creator["record_number"],
        "full_name": creator["full_name"],
    }

    for record, prefix in (
        (identity_graph["project"], "PRJ"),
        (identity_graph["requirement"], "REQ"),
        (identity_graph["story"], "US"),
    ):
        assert_record_number(record["record_number"], prefix)
        assert record["created_by"] == expected_creator

    with SessionLocal() as db:
        assert db.get(Project, UUID(identity_graph["project"]["id"])).created_by_id == creator["id"]
        assert (
            db.get(Requirement, UUID(identity_graph["requirement"]["id"])).created_by_id
            == creator["id"]
        )
        assert db.get(UserStory, UUID(identity_graph["story"]["id"])).created_by_id == creator["id"]


def test_read_list_and_detail_responses_include_creator_display(identity_graph, client):
    """I verify read endpoints preserve record numbers and creator display data."""

    creator = identity_graph["creator"]
    expected_creator = {
        "record_number": creator["record_number"],
        "full_name": creator["full_name"],
    }
    project = identity_graph["project"]
    requirement = identity_graph["requirement"]
    story = identity_graph["story"]
    headers = creator["headers"]

    responses = [
        client.get(f"{PROJECTS_URL}/{project['id']}", headers=headers),
        client.get(f"{REQUIREMENTS_URL}/{requirement['id']}", headers=headers),
        client.get(f"{STORIES_URL}/{story['id']}", headers=headers),
    ]
    for response, expected in zip(responses, (project, requirement, story)):
        assert response.status_code == 200, response.text
        assert response.json()["record_number"] == expected["record_number"]
        assert response.json()["created_by"] == expected_creator

    list_responses = [
        client.get(PROJECTS_URL, headers=headers),
        client.get(
            REQUIREMENTS_URL,
            params={"project_id": project["id"]},
            headers=headers,
        ),
        client.get(
            STORIES_URL,
            params={"requirement_id": requirement["id"]},
            headers=headers,
        ),
    ]
    for response in list_responses:
        assert response.status_code == 200, response.text
    list_payloads = [response.json()["items"] for response in list_responses]
    for items, expected in zip(list_payloads, (project, requirement, story)):
        found = next(item for item in items if item["id"] == expected["id"])
        assert found["record_number"] == expected["record_number"]
        assert found["created_by"] == expected_creator


def test_historical_null_creators_serialize_as_null(persisted_user, client):
    """I verify records without ownership retain a null creator response."""

    with SessionLocal() as db:
        project = Project(name=f"Historical Project {uuid4().hex}", status="planned")
        db.add(project)
        db.flush()
        requirement = Requirement(
            project_id=project.id,
            title="Historical Requirement",
            description="This predates creator attribution.",
            priority="medium",
            status="draft",
        )
        db.add(requirement)
        db.flush()
        story = UserStory(
            requirement_id=requirement.id,
            title="Historical User Story",
            description="This predates creator attribution.",
            acceptance_criteria=["Historical data remains readable."],
            status="draft",
        )
        db.add(story)
        db.commit()
        db.refresh(project)
        db.refresh(requirement)
        db.refresh(story)
        project_id, requirement_id, story_id = project.id, requirement.id, story.id

    try:
        headers = persisted_user["headers"]
        for url in (
            f"{PROJECTS_URL}/{project_id}",
            f"{REQUIREMENTS_URL}/{requirement_id}",
            f"{STORIES_URL}/{story_id}",
        ):
            response = client.get(url, headers=headers)
            assert response.status_code == 200, response.text
            assert response.json()["created_by"] is None

        list_responses = [
            client.get(PROJECTS_URL, headers=headers),
            client.get(
                REQUIREMENTS_URL,
                params={"project_id": str(project_id)},
                headers=headers,
            ),
            client.get(
                STORIES_URL,
                params={"requirement_id": str(requirement_id)},
                headers=headers,
            ),
        ]
        for response, record_id in zip(
            list_responses,
            (project_id, requirement_id, story_id),
        ):
            assert response.status_code == 200, response.text
            record = next(item for item in response.json()["items"] if item["id"] == str(record_id))
            assert record["created_by"] is None
    finally:
        with SessionLocal() as db:
            project = db.get(Project, project_id)
            if project is not None:
                db.delete(project)
                db.commit()


def test_patch_responses_preserve_record_numbers_and_creators(identity_graph, client):
    """I verify PATCH changes do not replace public record identity or creator."""

    creator = identity_graph["creator"]
    expected_creator = {
        "record_number": creator["record_number"],
        "full_name": creator["full_name"],
    }
    mutations = (
        (PROJECTS_URL, identity_graph["project"], {"description": "Updated project."}),
        (REQUIREMENTS_URL, identity_graph["requirement"], {"priority": "critical"}),
        (STORIES_URL, identity_graph["story"], {"title": "Updated Identity User Story"}),
    )

    for base_url, record, payload in mutations:
        response = client.patch(
            f"{base_url}/{record['id']}",
            json=payload,
            headers=creator["headers"],
        )
        assert response.status_code == 200, response.text
        assert response.json()["record_number"] == record["record_number"]
        assert response.json()["created_by"] == expected_creator


@pytest.mark.parametrize(
    ("url", "payload"),
    [
        (PROJECTS_URL, {"name": "Spoofed Project"}),
        (
            REQUIREMENTS_URL,
            {"project_id": str(uuid4()), "title": "Spoofed", "description": "Spoofed"},
        ),
        (
            STORIES_URL,
            {
                "requirement_id": str(uuid4()),
                "title": "Spoofed",
                "description": "Spoofed",
                "acceptance_criteria": ["Spoofed"],
            },
        ),
    ],
)
@pytest.mark.parametrize(
    ("identity_field", "identity_value"),
    [
        ("record_number", "USR-999"),
        ("created_by", {"record_number": "USR-999", "full_name": "Spoofed"}),
        ("created_by_id", str(uuid4())),
    ],
)
def test_create_requests_reject_identity_spoofing(
    client,
    persisted_user,
    url,
    payload,
    identity_field,
    identity_value,
):
    """I verify clients cannot submit record or creator identity fields."""

    response = client.post(
        url,
        headers=persisted_user["headers"],
        json={**payload, identity_field: identity_value},
    )

    assert response.status_code == 422


def test_record_numbers_are_unique_and_immutable_through_api(identity_graph, client):
    """I verify generated project numbers are unique and cannot be patched."""

    creator = identity_graph["creator"]
    first = identity_graph["project"]
    second_response = client.post(
        PROJECTS_URL,
        headers=creator["headers"],
        json={"name": f"Second Identity Project {uuid4().hex}"},
    )
    assert second_response.status_code == 201, second_response.text
    second = second_response.json()

    try:
        assert_record_number(second["record_number"], "PRJ")
        assert second["record_number"] != first["record_number"]

        mutation = client.patch(
            f"{PROJECTS_URL}/{first['id']}",
            headers=creator["headers"],
            json={"record_number": "PRJ-999"},
        )
        assert mutation.status_code == 422

        detail = client.get(
            f"{PROJECTS_URL}/{first['id']}",
            headers=creator["headers"],
        )
        assert detail.status_code == 200
        assert detail.json()["record_number"] == first["record_number"]
    finally:
        with SessionLocal() as db:
            project = db.get(Project, UUID(second["id"]))
            if project is not None:
                db.delete(project)
                db.commit()


def test_approval_rejection_and_audit_preserve_creator_and_actor_snapshots(
    identity_graph,
    client,
):
    """I verify approvals keep creators while audits retain the deciding actor."""

    creator = identity_graph["creator"]
    with SessionLocal() as db:
        reviewer = User(
            email=f"identity-reviewer-{uuid4().hex}@example.com",
            full_name="Identity Review User",
            password_hash="test-only-not-for-login",
            role="reviewer",
            is_active=True,
        )
        db.add(reviewer)
        db.commit()
        db.refresh(reviewer)
        reviewer_id = reviewer.id

    created_story_ids = [UUID(identity_graph["story"]["id"])]
    try:
        for action in ("approve", "reject"):
            expected_status = "approved" if action == "approve" else "rejected"
            if action == "approve":
                story = identity_graph["story"]
            else:
                creation = client.post(
                    STORIES_URL,
                    headers=creator["headers"],
                    json={
                        "requirement_id": identity_graph["requirement"]["id"],
                        "title": f"{action.title()} Identity Story",
                        "description": "A separately reviewed identity story.",
                        "acceptance_criteria": ["The review decision is audited."],
                        "status": "draft",
                    },
                )
                assert creation.status_code == 201, creation.text
                story = creation.json()
                created_story_ids.append(UUID(story["id"]))

            review = client.patch(
                f"{STORIES_URL}/{story['id']}",
                headers=creator["headers"],
                json={"status": "in_review"},
            )
            assert review.status_code == 200, review.text

            unauthorized_decision = client.post(
                f"{STORIES_URL}/{story['id']}/{action}",
                headers=creator["headers"],
            )
            assert unauthorized_decision.status_code == 403

            decision = client.post(
                f"{STORIES_URL}/{story['id']}/{action}",
                headers=headers_for(reviewer_id),
            )
            assert decision.status_code == 200, decision.text
            decision_data = decision.json()
            assert decision_data["status"] == expected_status
            assert decision_data["created_by"] == {
                "record_number": creator["record_number"],
                "full_name": creator["full_name"],
            }

            denied = client.get(
                f"{STORIES_URL}/{story['id']}/audit",
                headers=creator["headers"],
            )
            assert denied.status_code == 403
            audit_response = client.get(
                f"{STORIES_URL}/{story['id']}/audit",
                headers=headers_for(reviewer_id),
            )
            assert audit_response.status_code == 200, audit_response.text
            audit = next(
                item for item in audit_response.json()["items"] if item["action"] == expected_status
            )
            assert audit["user_story_id_snapshot"] == story["id"]
            assert audit["actor_id_snapshot"] == str(reviewer_id)
    finally:
        with SessionLocal() as db:
            for story_id in created_story_ids:
                db.execute(
                    UserStoryApprovalAudit.__table__.delete().where(
                        UserStoryApprovalAudit.user_story_id_snapshot == story_id
                    )
                )
            db.commit()
            reviewer = db.get(User, reviewer_id)
            if reviewer is not None:
                db.delete(reviewer)
                db.commit()
