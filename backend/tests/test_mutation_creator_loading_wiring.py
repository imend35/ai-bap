"""I verify mutation-response creator loading without runtime router imports."""

import ast
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse
from app.schemas.user_story import UserStoryResponse

BACKEND_ROOT = Path(__file__).resolve().parents[1]
CREATED_AT = datetime(2026, 10, 16, 12, 0, tzinfo=UTC)


def get_function_source(router_name: str, function_name: str) -> ast.FunctionDef:
    """I retrieve a route handler without loading application settings."""
    source_path = BACKEND_ROOT / "app" / "routers" / router_name
    module = ast.parse(source_path.read_text(encoding="utf-8"))

    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return node

    raise AssertionError(f"Route handler {function_name!r} was not found.")


@pytest.mark.parametrize(
    ("router_name", "function_name", "model_name"),
    [
        ("projects.py", "update_project", "Project"),
        ("requirements.py", "update_requirement", "Requirement"),
        ("user_stories.py", "update_user_story", "UserStory"),
        ("user_story_approvals.py", "approve_user_story", "UserStory"),
        ("user_story_approvals.py", "reject_user_story", "UserStory"),
    ],
)
def test_mutation_handlers_eager_load_creators_for_responses(
    router_name: str,
    function_name: str,
    model_name: str,
) -> None:
    """I reload each committed record with its creator relationship."""
    function = get_function_source(router_name, function_name)
    selectinload_arguments = [
        ast.unparse(node.args[0])
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "selectinload"
        and node.args
    ]

    assert selectinload_arguments == [f"{model_name}.created_by"]
    assert "created_by_id" not in ast.unparse(function)


@pytest.mark.parametrize(
    ("schema", "source"),
    [
        (
            ProjectResponse,
            SimpleNamespace(
                id=uuid4(),
                record_number="PRJ-003",
                created_by=SimpleNamespace(
                    record_number="USR-003",
                    full_name="Grace Hopper",
                ),
                name="Updated Project",
                description=None,
                status="active",
                created_at=CREATED_AT,
                updated_at=CREATED_AT,
            ),
        ),
        (
            RequirementResponse,
            SimpleNamespace(
                id=uuid4(),
                record_number="REQ-003",
                created_by=None,
                project_id=uuid4(),
                title="Historical Requirement",
                description="The creator is intentionally unknown.",
                priority="medium",
                status="in_review",
                created_at=CREATED_AT,
                updated_at=CREATED_AT,
            ),
        ),
        (
            UserStoryResponse,
            SimpleNamespace(
                id=uuid4(),
                record_number="US-003",
                created_by=SimpleNamespace(
                    record_number="USR-004",
                    full_name="Margaret Hamilton",
                ),
                requirement_id=uuid4(),
                title="Approved Story",
                description="A reviewed response preserves its creator.",
                acceptance_criteria=[],
                status="approved",
                created_at=CREATED_AT,
                updated_at=CREATED_AT,
            ),
        ),
    ],
)
def test_mutation_response_schemas_preserve_creator_or_historical_null(
    schema: type[ProjectResponse | RequirementResponse | UserStoryResponse],
    source: SimpleNamespace,
) -> None:
    """I serialize reloaded creator relationships without exposing creator UUIDs."""
    data = schema.model_validate(source).model_dump(mode="json")

    assert "created_by_id" not in data
    if source.created_by is None:
        assert data["created_by"] is None
    else:
        assert data["created_by"]["record_number"] == source.created_by.record_number
        assert data["created_by"]["full_name"] == source.created_by.full_name
