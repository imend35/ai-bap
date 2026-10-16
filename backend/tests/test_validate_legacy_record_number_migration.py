"""Unit tests for read-only legacy migration validation result handling."""

from collections.abc import Iterator
from typing import Any, Self

from scripts import validate_legacy_record_number_migration as validator
from scripts.seed_legacy_record_number_fixture import APPROVAL_AUDITS, REQUIREMENTS, USER_STORIES


class MappingOnlyResult:
    """Model a CursorResult that must be consumed through mappings().all()."""

    def __init__(
        self,
        rows: list[dict[str, Any]],
        raw_rows: list[tuple[str, Any]] | None = None,
    ) -> None:
        self.rows = rows
        self.raw_rows = raw_rows
        self.mappings_called = False

    def mappings(self) -> "MappingOnlyResult":
        self.mappings_called = True
        return self

    def all(self) -> list[dict[str, Any]]:
        return self.rows

    def __iter__(self) -> Iterator[object]:
        if self.raw_rows is None:
            yield self
            return
        yield from self.raw_rows

    def __getitem__(self, index: int) -> Any:
        raise TypeError("'CursorResult' object is not subscriptable")


class RelationshipConnection:
    """Return result sets in the order used by the relationship validator."""

    def __init__(self, results: list[MappingOnlyResult]) -> None:
        self.results = results

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def execute(self, *_: object, **__: object) -> MappingOnlyResult:
        return self.results.pop(0)


class RelationshipEngine:
    """Provide the minimal engine interface needed for this database-independent test."""

    def __init__(self, connection: RelationshipConnection) -> None:
        self.connection = connection

    def connect(self) -> RelationshipConnection:
        return self.connection


def test_relationship_check_consumes_cursor_results_as_mappings() -> None:
    """I verify CursorResults are materialized before relationship comparison."""
    results = [
        MappingOnlyResult(
            [{"id": row["id"], "project_id": row["project_id"]} for row in REQUIREMENTS],
            [(row["id"], row["project_id"]) for row in REQUIREMENTS],
        ),
        MappingOnlyResult(
            [{"id": row["id"], "requirement_id": row["requirement_id"]} for row in USER_STORIES],
            [(row["id"], row["requirement_id"]) for row in USER_STORIES],
        ),
        MappingOnlyResult(
            [{"id": row["id"], "status": row["status"]} for row in USER_STORIES],
            [(row["id"], row["status"]) for row in USER_STORIES],
        ),
        MappingOnlyResult([dict(row) for row in APPROVAL_AUDITS]),
    ]
    engine = RelationshipEngine(RelationshipConnection(results))

    checks = validator.check_relationships_and_audits(engine)  # type: ignore[arg-type]

    assert all(check.passed for check in checks)
    assert all(result.mappings_called for result in results)


def test_main_returns_nonzero_when_a_validation_check_fails(monkeypatch) -> None:
    """I verify failed validations retain their nonzero command exit status."""
    monkeypatch.setattr(
        validator,
        "check_environment",
        lambda _: [validator.CheckResult("preflight", False, "expected failure")],
    )

    assert validator.main() == 1
