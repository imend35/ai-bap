"""I verify eager creator-loading wiring without importing router dependencies."""

import ast
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def get_function_source(router_name: str, function_name: str) -> ast.FunctionDef:
    """I retrieve a route handler without importing application settings."""
    source_path = BACKEND_ROOT / "app" / "routers" / router_name
    module = ast.parse(source_path.read_text(encoding="utf-8"))

    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return node

    raise AssertionError(f"Route handler {function_name!r} was not found.")


@pytest.mark.parametrize(
    ("router_name", "function_name", "model_name"),
    [
        ("projects.py", "list_projects", "Project"),
        ("projects.py", "get_project", "Project"),
        ("requirements.py", "list_requirements", "Requirement"),
        ("requirements.py", "get_requirement", "Requirement"),
        ("user_stories.py", "list_user_stories", "UserStory"),
        ("user_stories.py", "get_user_story", "UserStory"),
    ],
)
def test_read_handlers_eager_load_creator_relationships(
    router_name: str,
    function_name: str,
    model_name: str,
) -> None:
    """I load each record creator before Pydantic serializes the response."""
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
