"""I verify migration failures do not disclose deployment configuration."""

from __future__ import annotations

import importlib.util
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Self

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_SCRIPT = PROJECT_ROOT / "docker" / "backend" / "migrate_production.py"
SENSITIVE_MARKER = "synthetic-secret-like-marker"


class FakeDatabaseUrl:
    """I provide a non-production URL interface for migration-script tests."""

    def set(self, **_kwargs: object) -> FakeDatabaseUrl:
        """I retain the test URL when the script selects the psycopg driver."""
        return self

    def render_as_string(self, *, hide_password: bool) -> str:
        """I return an in-memory test value that must never be emitted."""
        assert hide_password is False
        return f"postgresql://{SENSITIVE_MARKER}@test-host/test-database"


class FakeSettings:
    """I expose only the database URL interface used by the script."""

    database_url = FakeDatabaseUrl()


class FakeCursor:
    """I record advisory-lock SQL without connecting to PostgreSQL."""

    def __init__(self, failure: Exception | None = None) -> None:
        self.failure = failure
        self.statements: list[str] = []

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, statement: str, _parameters: tuple[int]) -> None:
        self.statements.append(statement)
        if self.failure is not None and "pg_advisory_lock" in statement:
            raise self.failure


class FakeConnection:
    """I provide the context-manager contract used by the migration script."""

    def __init__(self, cursor: FakeCursor) -> None:
        self.cursor_instance = cursor

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return self.cursor_instance


def load_migration_script():
    """Load the container script without executing it as a subprocess."""
    specification = importlib.util.spec_from_file_location(
        "migrate_production_for_test",
        MIGRATION_SCRIPT,
    )
    assert specification is not None
    assert specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def configure_successful_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    migration_module: object,
) -> FakeCursor:
    """Configure in-memory settings, connection, and Alembic success behavior."""
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(migration_module, "get_settings", lambda: FakeSettings())
    monkeypatch.setattr(
        migration_module.psycopg,
        "connect",
        lambda _url, *, autocommit: connection,
    )
    return cursor


def assert_sanitized_failure(captured: pytest.CaptureFixture[str]) -> None:
    """Assert that a failed migration emits only the fixed safe message."""
    output = captured.readouterr()

    assert output.out == ""
    assert output.err == "Database migration failed; the API will not start.\n"
    assert SENSITIVE_MARKER not in output.out
    assert SENSITIVE_MARKER not in output.err
    assert "Traceback" not in output.out
    assert "Traceback" not in output.err
    assert "postgresql://" not in output.out
    assert "postgresql://" not in output.err


def test_successful_migration_keeps_advisory_lock_and_upgrade_behavior(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """I retain the successful advisory-lock migration path."""
    migration = load_migration_script()
    cursor = configure_successful_dependencies(monkeypatch, migration)
    calls: list[tuple[list[str], bool, bool]] = []

    def run(command: list[str], *, check: bool, capture_output: bool) -> None:
        calls.append((command, check, capture_output))

    monkeypatch.setattr(migration.subprocess, "run", run)

    assert migration.main() == 0
    assert calls == [(["alembic", "upgrade", "head"], True, True)]
    assert cursor.statements == [
        "SELECT pg_advisory_lock(%s)",
        "SELECT pg_advisory_unlock(%s)",
    ]
    assert capsys.readouterr().out == "Alembic migrations applied successfully.\n"


@pytest.mark.parametrize(
    ("failure_stage", "configure_failure"),
    [
        (
            "invalid_configuration",
            lambda monkeypatch, migration: monkeypatch.setattr(
                migration,
                "get_settings",
                lambda: (_ for _ in ()).throw(RuntimeError(SENSITIVE_MARKER)),
            ),
        ),
        (
            "connection",
            lambda monkeypatch, migration: (
                configure_successful_dependencies(monkeypatch, migration),
                monkeypatch.setattr(
                    migration.psycopg,
                    "connect",
                    lambda _url, *, autocommit: (_ for _ in ()).throw(
                        OSError(SENSITIVE_MARKER)
                    ),
                ),
            ),
        ),
        (
            "advisory_lock",
            lambda monkeypatch, migration: (
                monkeypatch.setattr(migration, "get_settings", lambda: FakeSettings()),
                monkeypatch.setattr(
                    migration.psycopg,
                    "connect",
                    lambda _url, *, autocommit: FakeConnection(
                        FakeCursor(RuntimeError(SENSITIVE_MARKER))
                    ),
                ),
            ),
        ),
        (
            "alembic",
            lambda monkeypatch, migration: (
                configure_successful_dependencies(monkeypatch, migration),
                monkeypatch.setattr(
                    migration.subprocess,
                    "run",
                    lambda *_args, **_kwargs: (_ for _ in ()).throw(
                        subprocess.CalledProcessError(
                            1,
                            ["alembic", "upgrade", "head"],
                            output=SENSITIVE_MARKER,
                            stderr=SENSITIVE_MARKER,
                        )
                    ),
                ),
            ),
        ),
        (
            "unexpected",
            lambda monkeypatch, migration: (
                configure_successful_dependencies(monkeypatch, migration),
                monkeypatch.setattr(
                    migration.subprocess,
                    "run",
                    lambda *_args, **_kwargs: (_ for _ in ()).throw(
                        LookupError(SENSITIVE_MARKER)
                    ),
                ),
            ),
        ),
    ],
)
def test_migration_failures_are_nonzero_and_emit_only_fixed_safe_output(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    failure_stage: str,
    configure_failure: Callable[[pytest.MonkeyPatch, object], object],
) -> None:
    """I fail closed without relaying exception text from every failure stage."""
    migration = load_migration_script()
    configure_failure(monkeypatch, migration)

    assert migration.main() == 1, failure_stage
    assert_sanitized_failure(capsys)
