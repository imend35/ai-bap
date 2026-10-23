"""I verify the free Render deployment path without contacting a database."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FREE_BLUEPRINT = PROJECT_ROOT / "render.free.yaml"
DOCKERFILE = PROJECT_ROOT / "docker" / "backend" / "Dockerfile"
FREE_STARTUP_WRAPPER = PROJECT_ROOT / "docker" / "backend" / "start_api_free.py"


def load_free_startup_wrapper():
    """Load the container entrypoint script without executing it as a process."""
    specification = importlib.util.spec_from_file_location(
        "start_api_free_for_test",
        FREE_STARTUP_WRAPPER,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_free_blueprint_uses_free_resources_without_a_predeploy_command() -> None:
    """I keep the Free plan separate from paid-only Render pre-deploy behavior."""
    blueprint = yaml.safe_load(FREE_BLUEPRINT.read_text(encoding="utf-8"))

    database = blueprint["databases"][0]
    api = next(
        service for service in blueprint["services"] if service["name"] == "ai-bap-free-api"
    )
    frontend = next(
        service for service in blueprint["services"] if service["name"] == "ai-bap-free-frontend"
    )

    assert database["plan"] == "free"
    assert api["plan"] == "free"
    assert api["healthCheckPath"] == "/api/v1/health"
    assert api["dockerCommand"] == "python /usr/local/bin/start_api_free.py"
    assert "preDeployCommand" not in api
    assert api["autoDeployTrigger"] == "off"
    assert frontend["runtime"] == "static"
    assert frontend["autoDeployTrigger"] == "off"


def test_free_blueprint_uses_managed_database_and_public_api_references() -> None:
    """I retain private database access and an explicit public API build value."""
    blueprint = yaml.safe_load(FREE_BLUEPRINT.read_text(encoding="utf-8"))
    api = next(
        service for service in blueprint["services"] if service["name"] == "ai-bap-free-api"
    )
    frontend = next(
        service for service in blueprint["services"] if service["name"] == "ai-bap-free-frontend"
    )
    api_environment = {variable["key"]: variable for variable in api["envVars"]}
    frontend_environment = {variable["key"]: variable for variable in frontend["envVars"]}

    assert api_environment["DATABASE_URL"]["fromDatabase"] == {
        "name": "ai-bap-free-postgres",
        "property": "connectionString",
    }
    assert api_environment["JWT_SECRET_KEY"]["generateValue"] is True
    assert api_environment["CORS_ORIGINS"]["sync"] is False
    assert frontend_environment["VITE_API_BASE_URL"]["fromService"] == {
        "name": "ai-bap-free-api",
        "type": "web",
        "envVarKey": "RENDER_EXTERNAL_URL",
    }


def test_dockerfile_includes_the_free_startup_wrapper_without_changing_default_startup() -> None:
    """I keep local Compose and the paid Dockerfile command on the existing path."""
    dockerfile = DOCKERFILE.read_text(encoding="utf-8")

    assert (
        "COPY docker/backend/start_api_free.py /usr/local/bin/start_api_free.py" in dockerfile
    )
    assert 'CMD ["python", "/usr/local/bin/start_api.py"]' in dockerfile


def test_free_startup_wrapper_runs_migration_before_replacing_with_the_api(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """I delegate migration, bootstrap, and API startup to dedicated scripts."""
    wrapper = load_free_startup_wrapper()
    calls: list[tuple[str, object]] = []

    def record_migration(command: list[str], *, check: bool) -> None:
        calls.append(("migration", (command, check)))

    def record_api_start(executable: str, arguments: list[str]) -> None:
        calls.append(("api", (executable, arguments)))
        raise SystemExit(0)

    monkeypatch.setattr(wrapper.subprocess, "run", record_migration)
    monkeypatch.setattr(wrapper.os, "execv", record_api_start)

    with pytest.raises(SystemExit, match="0"):
        wrapper.main()

    assert calls == [
        ("migration", ([sys.executable, wrapper.MIGRATION_SCRIPT], True)),
        (
            "migration",
            ([sys.executable, wrapper.INITIAL_ADMIN_BOOTSTRAP_SCRIPT], True),
        ),
        ("api", (sys.executable, [sys.executable, wrapper.API_START_SCRIPT])),
    ]


def test_free_startup_wrapper_does_not_start_the_api_after_migration_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """I return a nonzero result and never start Uvicorn after a failed migration."""
    wrapper = load_free_startup_wrapper()

    def fail_migration(command: list[str], *, check: bool) -> None:
        raise subprocess.CalledProcessError(7, command)

    def unexpected_api_start(*_args: object) -> None:
        pytest.fail("The API start script must not run after migration failure.")

    monkeypatch.setattr(wrapper.subprocess, "run", fail_migration)
    monkeypatch.setattr(wrapper.os, "execv", unexpected_api_start)

    assert wrapper.main() == 7


def test_free_startup_wrapper_hides_child_failure_details(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """I keep a failed migration from relaying child-process diagnostic output."""
    wrapper = load_free_startup_wrapper()
    sensitive_marker = "synthetic-secret-like-marker"

    def fail_migration(command: list[str], *, check: bool) -> None:
        raise subprocess.CalledProcessError(
            7,
            command,
            output=sensitive_marker,
            stderr=sensitive_marker,
        )

    def unexpected_api_start(*_args: object) -> None:
        pytest.fail("The API start script must not run after migration failure.")

    monkeypatch.setattr(wrapper.subprocess, "run", fail_migration)
    monkeypatch.setattr(wrapper.os, "execv", unexpected_api_start)

    assert wrapper.main() == 7
    output = capsys.readouterr()
    assert output.out == ""
    assert output.err == "Database migration failed; the API will not start.\n"
    assert sensitive_marker not in output.out
    assert sensitive_marker not in output.err


def test_free_startup_wrapper_does_not_start_the_api_after_bootstrap_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """I stop before Uvicorn when the explicit bootstrap process fails."""
    wrapper = load_free_startup_wrapper()
    calls: list[list[str]] = []

    def run_step(command: list[str], *, check: bool) -> None:
        calls.append(command)
        if command[1] == wrapper.INITIAL_ADMIN_BOOTSTRAP_SCRIPT:
            raise subprocess.CalledProcessError(8, command)

    def unexpected_api_start(*_args: object) -> None:
        pytest.fail("The API start script must not run after bootstrap failure.")

    monkeypatch.setattr(wrapper.subprocess, "run", run_step)
    monkeypatch.setattr(wrapper.os, "execv", unexpected_api_start)

    assert wrapper.main() == 8
    assert calls == [
        [sys.executable, wrapper.MIGRATION_SCRIPT],
        [sys.executable, wrapper.INITIAL_ADMIN_BOOTSTRAP_SCRIPT],
    ]


def test_free_startup_wrapper_excludes_fresh_database_initialization() -> None:
    """I do not use the Compose-only fresh-database initializer in Free startup."""
    wrapper_source = FREE_STARTUP_WRAPPER.read_text(encoding="utf-8").lower()

    assert "initialize_fresh_database" not in wrapper_source
