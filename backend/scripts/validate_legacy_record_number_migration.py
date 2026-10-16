"""Validate the read-only outcome of the legacy record-number migration.

This script deliberately reads connection values only from the process environment.
It does not import application settings, so it never loads an application ``.env`` file.
"""

from __future__ import annotations

import hmac
import os
from collections.abc import Mapping
from dataclasses import dataclass

from sqlalchemy import URL, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.test_database_safety import (
    LEGACY_MIGRATION_TEST_CONFIRMATION_VALUE,
    LEGACY_MIGRATION_TEST_DATABASE_SETTINGS,
    LEGACY_MIGRATION_TEST_TARGET,
    TEST_MODE_VALUE,
    IntegrationDatabaseSafetyError,
    configure_legacy_migration_test_database_environment,
    validate_effective_test_database_target,
)
from scripts.seed_legacy_record_number_fixture import (
    APPROVAL_AUDITS,
    PROJECTS,
    REQUIREMENTS,
    USER_STORIES,
    USERS,
)

REQUIRED_REVISION = "c7a8d9e0f1b2"
ENTITY_CONFIG = (
    ("users", "USR", "users_record_number_seq"),
    ("projects", "PRJ", "projects_record_number_seq"),
    ("requirements", "REQ", "requirements_record_number_seq"),
    ("user_stories", "US", "user_stories_record_number_seq"),
)
FIXTURE_CONFIG = (
    ("users", USERS),
    ("projects", PROJECTS),
    ("requirements", REQUIREMENTS),
    ("user_stories", USER_STORIES),
    ("user_story_approval_audits", APPROVAL_AUDITS),
)


@dataclass(frozen=True)
class CheckResult:
    """Represent one validation result without exposing sensitive configuration."""

    name: str
    passed: bool
    detail: str


def check_environment(environment: Mapping[str, str]) -> list[CheckResult]:
    """Validate the approved target and credentials without printing secrets."""
    results = [
        CheckResult(
            "test mode acknowledgment",
            environment.get("AI_BAP_TEST_MODE") == TEST_MODE_VALUE,
            "AI_BAP_TEST_MODE must be true.",
        ),
        CheckResult(
            "legacy target selector",
            environment.get("AI_BAP_ALEMBIC_TARGET") == LEGACY_MIGRATION_TEST_TARGET,
            "AI_BAP_ALEMBIC_TARGET must select legacy-migration.",
        ),
        CheckResult(
            "legacy database acknowledgment",
            environment.get("AI_BAP_LEGACY_TEST_DATABASE_CONFIRMATION")
            == LEGACY_MIGRATION_TEST_CONFIRMATION_VALUE,
            "The explicit legacy database acknowledgment is required.",
        ),
    ]
    for setting_name, expected_value in LEGACY_MIGRATION_TEST_DATABASE_SETTINGS.items():
        results.append(
            CheckResult(
                f"exact {setting_name} target",
                environment.get(setting_name) == expected_value,
                f"{setting_name} must target the approved isolated database.",
            )
        )

    expected_password = environment.get("AI_BAP_LEGACY_TEST_POSTGRES_PASSWORD")
    supplied_password = environment.get("POSTGRES_PASSWORD")
    results.append(
        CheckResult(
            "password presence and match",
            bool(expected_password)
            and bool(supplied_password)
            and hmac.compare_digest(expected_password or "", supplied_password or ""),
            "POSTGRES_PASSWORD must match the explicit legacy test password.",
        )
    )
    return results


def build_read_only_engine(environment: Mapping[str, str]) -> Engine:
    """Create a connection factory that defaults every session to read-only."""
    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=environment["POSTGRES_USER"],
        password=environment["POSTGRES_PASSWORD"],
        host=environment["POSTGRES_HOST"],
        port=int(environment["POSTGRES_PORT"]),
        database=environment["POSTGRES_DB"],
    )
    validate_effective_test_database_target(database_url, LEGACY_MIGRATION_TEST_TARGET)
    return create_engine(
        database_url,
        connect_args={"options": "-c default_transaction_read_only=on"},
    )


def check_revision(engine: Engine) -> CheckResult:
    """Require precisely the migration revision under validation."""
    with engine.connect() as connection:
        actual_revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
    return CheckResult(
        "Alembic revision",
        actual_revision == REQUIRED_REVISION,
        f"Expected {REQUIRED_REVISION}; found {actual_revision!r}.",
    )


def check_fixture_records(engine: Engine) -> list[CheckResult]:
    """Confirm every fixture row remains with its original deterministic UUID."""
    results: list[CheckResult] = []
    with engine.connect() as connection:
        for table_name, fixture_rows in FIXTURE_CONFIG:
            expected_ids = {row["id"] for row in fixture_rows}
            actual_ids = set(
                connection.scalars(
                    text(f"SELECT id FROM {table_name} WHERE id = ANY(:ids)"),
                    {"ids": list(expected_ids)},
                )
            )
            results.append(
                CheckResult(
                    f"synthetic {table_name} UUIDs",
                    actual_ids == expected_ids,
                    f"Expected {len(expected_ids)} deterministic UUIDs; found {len(actual_ids)}.",
                )
            )
    return results


def check_relationships_and_audits(engine: Engine) -> list[CheckResult]:
    """Confirm legacy foreign keys, statuses, and immutable audit identities."""
    expected_relationships = {
        "requirements": {row["id"]: row["project_id"] for row in REQUIREMENTS},
        "user_stories": {row["id"]: row["requirement_id"] for row in USER_STORIES},
    }
    expected_story_statuses = {row["id"]: row["status"] for row in USER_STORIES}
    expected_audits = {
        row["id"]: (
            row["user_story_id"],
            row["actor_id"],
            row["user_story_id_snapshot"],
            row["actor_id_snapshot"],
            row["action"],
            row["previous_status"],
            row["new_status"],
        )
        for row in APPROVAL_AUDITS
    }
    with engine.connect() as connection:
        relationship_results = []
        for table_name, expected_rows in expected_relationships.items():
            column_name = "project_id" if table_name == "requirements" else "requirement_id"
            relationship_rows = (
                connection.execute(
                    text(f"SELECT id, {column_name} FROM {table_name} WHERE id = ANY(:ids)"),
                    {"ids": list(expected_rows)},
                )
                .mappings()
                .all()
            )
            actual_rows = {
                row["id"]: row[column_name]
                for row in relationship_rows
            }
            relationship_results.append(
                CheckResult(
                    f"{table_name} foreign-key relationships",
                    actual_rows == expected_rows,
                    "Legacy parent references must remain unchanged.",
                )
            )

        status_rows = (
            connection.execute(
                text("SELECT id, status FROM user_stories WHERE id = ANY(:ids)"),
                {"ids": list(expected_story_statuses)},
            )
            .mappings()
            .all()
        )
        actual_statuses = {row["id"]: row["status"] for row in status_rows}
        audit_rows = (
            connection.execute(
                text(
                    "SELECT id, user_story_id, actor_id, user_story_id_snapshot, "
                    "actor_id_snapshot, action, previous_status, new_status "
                    "FROM user_story_approval_audits WHERE id = ANY(:ids)"
                ),
                {"ids": list(expected_audits)},
            )
            .mappings()
            .all()
        )
        actual_audits = {
            row["id"]: (
                row["user_story_id"],
                row["actor_id"],
                row["user_story_id_snapshot"],
                row["actor_id_snapshot"],
                row["action"],
                row["previous_status"],
                row["new_status"],
            )
            for row in audit_rows
        }

    return [
        *relationship_results,
        CheckResult(
            "user story statuses",
            actual_statuses == expected_story_statuses,
            "Legacy approved and rejected statuses must remain unchanged.",
        ),
        CheckResult(
            "approval-audit actor references and identity snapshots",
            actual_audits == expected_audits,
            "Approval audits must retain actor references and UUID snapshots.",
        ),
    ]


def check_record_numbers_and_sequences(engine: Engine) -> list[CheckResult]:
    """Verify deterministic backfill values and collision-free sequence positions."""
    results: list[CheckResult] = []
    with engine.connect() as connection:
        for table_name, prefix, sequence_name in ENTITY_CONFIG:
            rows = connection.execute(
                text(f"SELECT id, created_at, record_number FROM {table_name} ORDER BY created_at, id")
            ).all()
            expected_numbers = {
                row.id: f"{prefix}-{position:03d}"
                for position, row in enumerate(rows, start=1)
            }
            actual_numbers = {row.id: row.record_number for row in rows}
            distinct_numbers = len(actual_numbers) == len(set(actual_numbers.values()))
            results.append(
                CheckResult(
                    f"{table_name} record-number uniqueness",
                    distinct_numbers,
                    "Every record_number must be unique.",
                )
            )
            results.append(
                CheckResult(
                    f"{table_name} deterministic record-number backfill",
                    actual_numbers == expected_numbers,
                    "record_number must follow created_at then UUID ordering.",
                )
            )

            sequence_row = connection.execute(
                text(f"SELECT last_value, is_called FROM {sequence_name}")
            ).one()
            next_value = sequence_row.last_value + (1 if sequence_row.is_called else 0)
            assigned_suffixes = [
                int(record_number.rsplit("-", maxsplit=1)[1])
                for record_number in actual_numbers.values()
                if record_number.startswith(f"{prefix}-")
                and record_number.rsplit("-", maxsplit=1)[1].isdigit()
            ]
            results.append(
                CheckResult(
                    f"{sequence_name} collision avoidance",
                    next_value > max(assigned_suffixes, default=0),
                    "The next sequence value must exceed every assigned suffix.",
                )
            )
    return results


def check_historical_creators(engine: Engine) -> list[CheckResult]:
    """Ensure the legacy records were not assigned a creator during migration."""
    results: list[CheckResult] = []
    with engine.connect() as connection:
        for table_name, fixture_rows in FIXTURE_CONFIG[1:4]:
            fixture_ids = [row["id"] for row in fixture_rows]
            non_null_count = connection.scalar(
                text(
                    f"SELECT COUNT(*) FROM {table_name} "
                    "WHERE id = ANY(:ids) AND created_by_id IS NOT NULL"
                ),
                {"ids": fixture_ids},
            )
            results.append(
                CheckResult(
                    f"historical {table_name}.created_by_id values",
                    non_null_count == 0,
                    "All synthetic legacy records must retain NULL created_by_id values.",
                )
            )
    return results


def print_report(results: list[CheckResult]) -> bool:
    """Print a clear, secret-free PASS/FAIL report and return the overall status."""
    print("Legacy migration validation report")
    all_passed = True
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status}: {result.name} — {result.detail}")
        all_passed = all_passed and result.passed
    print(f"OVERALL: {'PASS' if all_passed else 'FAIL'}")
    return all_passed


def main() -> int:
    """Run preflight checks before issuing only read-only validation queries."""
    environment_results = check_environment(os.environ)
    if not print_report(environment_results):
        return 1

    try:
        # Reuse the shared fail-closed guard before creating any database engine.
        configure_legacy_migration_test_database_environment()
        engine = build_read_only_engine(os.environ)
        results = [
            *environment_results,
            check_revision(engine),
            *check_fixture_records(engine),
            *check_relationships_and_audits(engine),
            *check_record_numbers_and_sequences(engine),
            *check_historical_creators(engine),
        ]
    except (IntegrationDatabaseSafetyError, SQLAlchemyError) as error:
        # The report must not expose connection details or secrets.
        results = [
            *environment_results,
            CheckResult("read-only database validation", False, type(error).__name__),
        ]
    return 0 if print_report(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
