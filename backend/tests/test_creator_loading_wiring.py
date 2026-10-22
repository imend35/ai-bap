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
    ("router_name", "function_name", "expected_relationships"),
    [
        (
            "projects.py",
            "list_projects",
            ["Project.created_by", "Project.archived_by"],
        ),
        ("requirements.py", "list_requirements", ["Requirement.created_by"]),
        ("requirements.py", "get_requirement", ["Requirement.created_by"]),
        ("user_stories.py", "list_user_stories", ["UserStory.created_by"]),
        ("user_stories.py", "get_user_story", ["UserStory.created_by"]),
    ],
)
def test_read_handlers_eager_load_creator_relationships(
    router_name: str,
    function_name: str,
    expected_relationships: list[str],
) -> None:
    """I load every response actor relationship before Pydantic serialization."""
    function = get_function_source(router_name, function_name)
    selectinload_arguments = [
        ast.unparse(node.args[0])
        for node in ast.walk(function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "selectinload"
        and node.args
    ]

    assert selectinload_arguments == expected_relationships


def test_project_detail_reuses_the_creator_and_archive_actor_loader() -> None:
    """I load project detail with every response actor relationship."""
    detail_function = get_function_source("projects.py", "get_project")
    loader_function = get_function_source(
        "projects.py",
        "get_project_with_relationships",
    )
    loader_relationships = [
        ast.unparse(node.args[0])
        for node in ast.walk(loader_function)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "selectinload"
        and node.args
    ]

    assert (
        ast.unparse(detail_function).count("get_project_with_relationships")
        == 1
    )
    assert loader_relationships == [
        "Project.created_by",
        "Project.archived_by",
    ]
