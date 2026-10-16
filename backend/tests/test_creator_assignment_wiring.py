"""I verify creator assignment wiring without importing the application runtime."""

import ast
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.project import ProjectCreate
from app.schemas.requirement import RequirementCreate
from app.schemas.user_story import UserStoryCreate

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def get_function_source(router_name: str, function_name: str) -> ast.FunctionDef:
    """I retrieve one route handler without importing router dependencies."""
    source_path = BACKEND_ROOT / "app" / "routers" / router_name
    module = ast.parse(source_path.read_text(encoding="utf-8"))

    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return node

    raise AssertionError(f"Route handler {function_name!r} was not found.")


@pytest.mark.parametrize(
    ("router_name", "function_name", "model_name"),
    [
        ("projects.py", "create_project", "Project"),
        ("requirements.py", "create_requirement", "Requirement"),
        ("user_stories.py", "create_user_story", "UserStory"),
    ],
)
def test_create_handlers_assign_creator_from_the_authenticated_user(
    router_name: str,
    function_name: str,
    model_name: str,
) -> None:
    """I assign creator ownership server-side for every authored record."""
    function = get_function_source(router_name, function_name)
    constructors = [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == model_name
    ]

    assert len(constructors) == 1
    creator_keyword = next(
        (
            keyword
            for keyword in constructors[0].keywords
            if keyword.arg == "created_by_id"
        ),
        None,
    )

    assert creator_keyword is not None
    assert ast.unparse(creator_keyword.value) == "current_user.id"


@pytest.mark.parametrize(
    ("router_name", "function_name"),
    [
        ("projects.py", "create_project"),
        ("requirements.py", "create_requirement"),
        ("user_stories.py", "create_user_story"),
    ],
)
def test_create_handlers_retain_existing_editor_role_requirements(
    router_name: str,
    function_name: str,
) -> None:
    """I require the existing admin-or-business-analyst dependency."""
    function = get_function_source(router_name, function_name)
    current_user = next(
        argument
        for argument in function.args.args
        if argument.arg == "current_user"
    )

    assert current_user.annotation is not None
    assert ast.unparse(current_user.annotation) == (
        "Annotated[User, Depends(require_roles(ADMIN, BUSINESS_ANALYST))]"
    )


@pytest.mark.parametrize(
    ("schema", "payload"),
    [
        (
            ProjectCreate,
            {
                "name": "Spoofed Project",
                "created_by": {"record_number": "USR-999", "full_name": "Spoof"},
            },
        ),
        (
            RequirementCreate,
            {
                "project_id": uuid4(),
                "title": "Spoofed Requirement",
                "description": "The client must not choose its creator.",
                "created_by_id": uuid4(),
            },
        ),
        (
            UserStoryCreate,
            {
                "requirement_id": uuid4(),
                "title": "Spoofed Story",
                "description": "The client must not choose its creator.",
                "acceptance_criteria": [],
                "record_number": "US-999",
            },
        ),
    ],
)
def test_create_requests_reject_client_supplied_identity_fields(
    schema: type[ProjectCreate | RequirementCreate | UserStoryCreate],
    payload: dict[str, object],
) -> None:
    """I forbid creator and record identity fields in client payloads."""
    with pytest.raises(ValidationError):
        schema.model_validate(payload)
