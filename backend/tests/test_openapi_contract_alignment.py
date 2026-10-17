"""I compare the checked-in OpenAPI contract with the FastAPI route schema."""

from pathlib import Path
from typing import Any

import pytest
import yaml

BACKEND_ROOT = Path(__file__).resolve().parents[1]
OPENAPI_PATH = BACKEND_ROOT.parent / "openapi.yaml"
JWT_SECURITY = [{"JWTBearer": []}]


@pytest.fixture(scope="module")
def checked_contract() -> dict[str, Any]:
    """I load the checked-in contract without starting application services."""
    return yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def runtime_contract() -> dict[str, Any]:
    """I generate FastAPI OpenAPI with dotenv loading disabled."""
    from app.config import Settings, get_settings

    original_env_file = Settings.model_config["env_file"]
    Settings.model_config["env_file"] = None

    try:
        import os

        os.environ["POSTGRES_PASSWORD"] = "contract-test-password"
        os.environ["JWT_SECRET_KEY"] = "contract-test-jwt-secret-key-000000000000"
        get_settings.cache_clear()

        from app.main import app

        app.openapi_schema = None
        return app.openapi()
    finally:
        Settings.model_config["env_file"] = original_env_file
        get_settings.cache_clear()


def response_reference(
    contract: dict[str, Any],
    path: str,
    method: str,
    status_code: str,
) -> str:
    """I return an operation response schema reference."""
    schema = contract["paths"][path][method]["responses"][status_code]["content"][
        "application/json"
    ]["schema"]
    return schema["$ref"]


def resolved_properties(
    contract: dict[str, Any],
    schema_name: str,
) -> tuple[dict[str, Any], set[str]]:
    """I resolve properties from a direct schema or its local allOf members."""
    schemas = contract["components"]["schemas"]
    schema = schemas[schema_name]
    members = schema.get("allOf", [schema])
    properties: dict[str, Any] = {}
    required: set[str] = set()

    for member in members:
        if "$ref" in member:
            member = schemas[member["$ref"].rsplit("/", maxsplit=1)[1]]
        properties.update(member.get("properties", {}))
        required.update(member.get("required", []))

    return properties, required


def effective_security(
    contract: dict[str, Any],
    operation: dict[str, Any],
) -> list[dict[str, list[str]]]:
    """I resolve operation security with the document-level default."""
    return operation.get("security", contract.get("security", []))


def test_checked_contract_is_valid_yaml(checked_contract: dict[str, Any]) -> None:
    """I keep the checked-in contract parseable as OpenAPI 3.1 YAML."""
    assert checked_contract["openapi"] == "3.1.0"
    assert isinstance(checked_contract["paths"], dict)


def test_checked_paths_match_runtime_paths(
    checked_contract: dict[str, Any],
    runtime_contract: dict[str, Any],
) -> None:
    """I keep the checked-in path inventory aligned with FastAPI."""
    assert set(checked_contract["paths"]) == set(runtime_contract["paths"])


def test_authentication_routes_match_runtime(
    checked_contract: dict[str, Any],
    runtime_contract: dict[str, Any],
) -> None:
    """I document the exact public and protected authentication routes."""
    for path, method, request_schema, response_schema, status_code in (
        ("/api/v1/auth/register", "post", "UserRegister", "UserResponse", "201"),
        ("/api/v1/auth/login", "post", "UserLogin", "TokenResponse", "200"),
    ):
        assert path in checked_contract["paths"]
        assert path in runtime_contract["paths"]
        assert (
            checked_contract["paths"][path][method]["requestBody"]["content"]
            ["application/json"]["schema"]["$ref"]
            == f"#/components/schemas/{request_schema}"
        )
        assert response_reference(checked_contract, path, method, status_code) == (
            f"#/components/schemas/{response_schema}"
        )
        assert response_reference(runtime_contract, path, method, status_code) == (
            f"#/components/schemas/{response_schema}"
        )
        assert effective_security(checked_contract, checked_contract["paths"][path][method]) == []

    profile_path = "/api/v1/auth/me"
    assert response_reference(checked_contract, profile_path, "get", "200") == (
        "#/components/schemas/UserResponse"
    )
    assert response_reference(runtime_contract, profile_path, "get", "200") == (
        "#/components/schemas/UserResponse"
    )
    assert effective_security(checked_contract, checked_contract["paths"][profile_path]["get"]) == JWT_SECURITY
    assert runtime_contract["paths"][profile_path]["get"]["security"] == JWT_SECURITY


def test_admin_user_routes_match_runtime(
    checked_contract: dict[str, Any],
    runtime_contract: dict[str, Any],
) -> None:
    """I document the administrator-only user-management routes."""
    expected = (
        ("/api/v1/admin/users", "get", "AdminUserListResponse"),
        ("/api/v1/admin/users/{user_id}", "get", "AdminUserResponse"),
    )

    for path, method, response_schema in expected:
        assert response_reference(checked_contract, path, method, "200") == (
            f"#/components/schemas/{response_schema}"
        )
        assert response_reference(runtime_contract, path, method, "200") == (
            f"#/components/schemas/{response_schema}"
        )
        assert effective_security(
            checked_contract,
            checked_contract["paths"][path][method],
        ) == JWT_SECURITY
        assert runtime_contract["paths"][path][method]["security"] == JWT_SECURITY

    create_path = "/api/v1/admin/users"
    assert response_reference(checked_contract, create_path, "post", "201") == (
        "#/components/schemas/AdminUserResponse"
    )
    assert response_reference(runtime_contract, create_path, "post", "201") == (
        "#/components/schemas/AdminUserResponse"
    )
    assert effective_security(
        checked_contract,
        checked_contract["paths"][create_path]["post"],
    ) == JWT_SECURITY
    assert runtime_contract["paths"][create_path]["post"]["security"] == JWT_SECURITY

    checked_create = checked_contract["components"]["schemas"]["AdminUserCreate"]
    runtime_create = runtime_contract["components"]["schemas"]["AdminUserCreate"]
    for create_schema in (checked_create, runtime_create):
        assert {"email", "full_name", "password"}.issubset(create_schema["required"])
        assert create_schema["properties"]["role"]["default"] == "business_analyst"
        assert create_schema["properties"]["is_active"]["default"] is True
        assert create_schema["properties"]["password"]["minLength"] == 12

    assert checked_create["additionalProperties"] is False
    assert checked_create["properties"]["password"]["writeOnly"] is True

    checked_user = checked_contract["components"]["schemas"]["AdminUserResponse"]
    runtime_user = runtime_contract["components"]["schemas"]["AdminUserResponse"]
    required_fields = {
        "id",
        "record_number",
        "email",
        "full_name",
        "role",
        "is_active",
        "created_at",
        "updated_at",
    }
    assert required_fields.issubset(checked_user["required"])
    assert required_fields.issubset(runtime_user["required"])
    assert checked_user["properties"]["record_number"]["readOnly"] is True
    assert checked_user["properties"]["record_number"]["pattern"] == "^USR-[0-9]{3,}$"


def test_identity_response_schemas_match_runtime_fields(
    checked_contract: dict[str, Any],
    runtime_contract: dict[str, Any],
) -> None:
    """I require immutable display numbers and nullable historical creators."""
    for schema_name, prefix in (
        ("UserResponse", "USR"),
        ("ProjectResponse", "PRJ"),
        ("RequirementResponse", "REQ"),
        ("UserStoryResponse", "US"),
    ):
        checked_properties, checked_required = resolved_properties(
            checked_contract,
            schema_name,
        )
        runtime_properties, runtime_required = resolved_properties(
            runtime_contract,
            schema_name,
        )

        assert "record_number" in checked_required
        assert "record_number" in runtime_required
        assert checked_properties["record_number"]["pattern"] == f"^{prefix}-[0-9]{{3,}}$"
        assert runtime_properties["record_number"]["pattern"] == f"^{prefix}-[0-9]{{3,}}$"

        if schema_name != "UserResponse":
            assert "created_by" in checked_required
            assert "created_by" in runtime_required
            assert checked_properties["created_by"]["anyOf"][-1] == {"type": "null"}
            assert runtime_properties["created_by"]["anyOf"][-1] == {"type": "null"}
            assert "historical records" in checked_properties["created_by"]["description"]

    creator = checked_contract["components"]["schemas"]["RecordCreator"]
    assert creator["required"] == ["record_number", "full_name"]
    assert creator["properties"]["record_number"]["pattern"] == "^USR-[0-9]{3,}$"


def test_identity_fields_are_response_only_and_requests_do_not_accept_them(
    checked_contract: dict[str, Any],
) -> None:
    """I prohibit client-provided record numbers and creator ownership."""
    for schema_name in (
        "ProjectCreate",
        "RequirementCreate",
        "UserStoryCreate",
        "ProjectUpdate",
        "RequirementUpdate",
        "UserStoryUpdate",
    ):
        properties = checked_contract["components"]["schemas"][schema_name]["properties"]
        assert {"record_number", "created_by", "created_by_id"}.isdisjoint(properties)


def test_story_generation_approval_and_audit_routes_match_runtime(
    checked_contract: dict[str, Any],
    runtime_contract: dict[str, Any],
) -> None:
    """I align the remaining user-story runtime paths and response schemas."""
    expected = (
        ("/api/v1/user-stories/generate", "post", "200", "AIUserStoryGenerateResponse"),
        ("/api/v1/user-stories/{story_id}/approve", "post", "200", "UserStoryResponse"),
        ("/api/v1/user-stories/{story_id}/reject", "post", "200", "UserStoryResponse"),
        ("/api/v1/user-stories/{story_id}/audit", "get", "200", "UserStoryApprovalAuditListResponse"),
    )

    for path, method, status_code, response_schema in expected:
        assert response_reference(checked_contract, path, method, status_code) == (
            f"#/components/schemas/{response_schema}"
        )
        assert response_reference(runtime_contract, path, method, status_code) == (
            f"#/components/schemas/{response_schema}"
        )
        assert effective_security(checked_contract, checked_contract["paths"][path][method]) == JWT_SECURITY
        assert runtime_contract["paths"][path][method]["security"] == JWT_SECURITY

    audit = checked_contract["components"]["schemas"]["UserStoryApprovalAuditResponse"]
    assert {"user_story_id_snapshot", "actor_id_snapshot"}.issubset(audit["properties"])


def test_intentional_documentation_enhancements_are_explicit(
    checked_contract: dict[str, Any],
    runtime_contract: dict[str, Any],
) -> None:
    """I retain useful contract metadata FastAPI cannot infer from handlers.

    The checked-in file centralizes JWT security at the document level, marks
    response-only identities read-only, and documents manually raised HTTP
    errors. FastAPI emits operation-level security and only auto-documents
    response models and validation errors unless handlers declare responses.
    """
    assert checked_contract["security"] == JWT_SECURITY
    assert "security" not in checked_contract["paths"]["/api/v1/auth/me"]["get"]
    assert runtime_contract["paths"]["/api/v1/auth/me"]["get"]["security"] == JWT_SECURITY
    assert checked_contract["components"]["schemas"]["UserResponse"]["properties"][
        "record_number"
    ]["readOnly"] is True
    assert "readOnly" not in runtime_contract["components"]["schemas"]["UserResponse"][
        "properties"
    ]["record_number"]
    assert "409" in checked_contract["paths"]["/api/v1/user-stories/{story_id}/approve"]["post"][
        "responses"
    ]
    assert "409" not in runtime_contract["paths"]["/api/v1/user-stories/{story_id}/approve"][
        "post"
    ]["responses"]
