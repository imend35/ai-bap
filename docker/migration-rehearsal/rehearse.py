"""Fail-closed, clone-specific migration rehearsal runner."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg

EXPECTED_ENDPOINT = ("127.0.0.1", "5432", "restore_check_db")
EXPECTED_SOURCE_REVISION = "921eeafe8be6"
TARGET_REVISION = "d4e5f6a7b8c9"
PASSWORD_FILE = Path("/run/secrets/restore_db_password")
PREFLIGHT_REPORT_FILE = Path("/run/rehearsal/preflight-report.json")
MIGRATIONS_DIRECTORY = Path("/workspace/migrations/versions")
ALEMBIC_CONFIG = "/workspace/rehearsal/alembic.ini"
TABLES = ("users", "projects", "requirements", "user_stories")
INTEGRITY_TABLES = (*TABLES, "user_story_approval_audits")
CREATOR_TABLES = ("projects", "requirements", "user_stories")
RECORD_NUMBER_CONFIG = (
    ("users", "USR", "users_record_number_seq"),
    ("projects", "PRJ", "projects_record_number_seq"),
    ("requirements", "REQ", "requirements_record_number_seq"),
    ("user_stories", "US", "user_stories_record_number_seq"),
)
EXPECTED_NEW_COLUMNS = {
    "users": frozenset({"record_number"}),
    "projects": frozenset({"record_number", "created_by_id"}),
    "requirements": frozenset({"record_number", "created_by_id"}),
    "user_stories": frozenset({"record_number", "created_by_id"}),
    "user_story_approval_audits": frozenset(),
}
SEQUENCE_MAXIMUM = 9223372036854775807
HARDENED_ASSIGNMENT_BODY = (
    "BEGIN "
    "IF NEW.record_number IS NOT NULL THEN "
    "RAISE EXCEPTION 'record_number is assigned by PostgreSQL'; "
    "END IF; "
    "NEW.record_number := '{prefix}-' || "
    "pg_catalog.lpad(pg_catalog.nextval('public.{sequence}'::pg_catalog.regclass)::text, 3, '0'); "
    "RETURN NEW; "
    "END;"
)
IMMUTABILITY_BODY = "BEGIN RAISE EXCEPTION 'record_number is immutable'; END;"
EXPECTED_MIGRATION_CHAIN = (
    (
        "921eeafe8be6_add_immutable_audit_identity_snapshots.py",
        "921eeafe8be6",
        "32937c1c1b14",
        "352d04ccf1103c89425b6604d318c2a3dfea112c18bb3c4645734bb3c653347c",
    ),
    (
        "c7a8d9e0f1b2_add_readable_record_numbers_and_creators.py",
        "c7a8d9e0f1b2",
        "921eeafe8be6",
        "8c6cf438e8194ba349f16cb8ce27117911f0116cadd8b6e4809baafecb569f13",
    ),
    (
        "d4e5f6a7b8c9_harden_record_number_trigger_functions.py",
        "d4e5f6a7b8c9",
        "c7a8d9e0f1b2",
        "8d731577ce3935ce8f8e74dbd9f063c7f542bd4e3c54b63723a02c347166fa0a",
    ),
)
REVISION_ASSIGNMENT = re.compile(r'^revision\s*:[^=\n]+\s*=\s*["\']([^"\']+)["\']\s*$', re.MULTILINE)
DOWN_REVISION_ASSIGNMENT = re.compile(
    r'^down_revision\s*:[^=\n]+\s*=\s*["\']([^"\']+)["\']\s*$', re.MULTILINE
)
SECURITY_FOLLOWUP_FRAGMENTS = (
    "CREATE OR REPLACE FUNCTION public.assign_",
    "SET search_path = pg_catalog",
    "pg_catalog.nextval(",
    "Downgrade of record-number trigger-function hardening is intentionally unsupported.",
)
FULL_CONTAINER_ID = re.compile(r"^[0-9a-f]{64}$")


class RehearsalError(RuntimeError):
    """Raise a safe, categorized failure without exposing operational details."""


class ConfigurationError(RehearsalError):
    """The helper was not configured for its one approved target."""


class PreflightError(RehearsalError):
    """The clone did not satisfy a required condition before migration."""


class PostflightError(RehearsalError):
    """The migrated clone did not satisfy every required invariant."""


class CanonicalizationError(RehearsalError):
    """A source value cannot be represented safely and deterministically."""


def required(name: str) -> str:
    """Return a required non-secret setting without logging its value."""
    value = os.environ.get(name)
    if not value:
        raise ConfigurationError("configuration_error")
    return value


def connection_kwargs(*, read_only: bool) -> dict[str, str | int]:
    """Read the clone-only password from its Docker secret mount."""
    if not PASSWORD_FILE.is_file():
        raise ConfigurationError("configuration_error")
    password = PASSWORD_FILE.read_text(encoding="utf-8").rstrip("\r\n")
    if not password:
        raise ConfigurationError("configuration_error")
    endpoint = (
        required("REHEARSAL_DATABASE_HOST"),
        required("REHEARSAL_DATABASE_PORT"),
        required("REHEARSAL_DATABASE_NAME"),
    )
    if endpoint != EXPECTED_ENDPOINT:
        raise ConfigurationError("configuration_error")
    try:
        port = int(endpoint[1])
    except ValueError as error:
        raise ConfigurationError("configuration_error") from error
    kwargs: dict[str, str | int] = {
        "host": endpoint[0],
        "port": port,
        "dbname": endpoint[2],
        "user": required("REHEARSAL_DATABASE_USER"),
        "password": password,
        "connect_timeout": 5,
    }
    if read_only:
        # Applied by PostgreSQL before the first query; do not rely solely on
        # this program's query list to keep validation stages non-mutating.
        kwargs["options"] = "-c default_transaction_read_only=on"
    return kwargs


def restore_container_id() -> str:
    """Require the immutable ID verified by the host launcher."""
    container_id = required("REHEARSAL_RESTORE_CONTAINER_ID")
    if FULL_CONTAINER_ID.fullmatch(container_id) is None:
        raise ConfigurationError("configuration_error")
    return container_id


def scalar(connection: psycopg.Connection[Any], query: str, parameters: tuple[Any, ...] = ()) -> Any:
    """Run a fixed read-only scalar query."""
    with connection.cursor() as cursor:
        cursor.execute(query, parameters)
        row = cursor.fetchone()
    return row[0] if row else None


def rows(connection: psycopg.Connection[Any], query: str, parameters: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    """Run a fixed read-only query and return rows without logging them."""
    with connection.cursor() as cursor:
        cursor.execute(query, parameters)
        return list(cursor.fetchall())


def normalize(value: Any) -> Any:
    """Encode only supported PostgreSQL values with explicit types."""
    if value is None:
        return ["null"]
    if isinstance(value, bool):
        return ["bool", value]
    if isinstance(value, (int, Decimal)):
        return [type(value).__name__, str(value)]
    if isinstance(value, float):
        return ["float", value.hex()]
    if isinstance(value, str):
        return ["str", value]
    if isinstance(value, UUID):
        return ["uuid", str(value)]
    if isinstance(value, datetime):
        return ["datetime", value.isoformat()]
    if isinstance(value, date):
        return ["date", value.isoformat()]
    if isinstance(value, time):
        return ["time", value.isoformat()]
    if isinstance(value, (bytes, memoryview)):
        return ["bytes", base64.b64encode(bytes(value)).decode("ascii")]
    if isinstance(value, list):
        return ["list", [normalize(item) for item in value]]
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return ["dict", [[key, normalize(value[key])] for key in sorted(value)]]
    raise CanonicalizationError("canonicalization_error")


def canonical_sql(value: str) -> str:
    """Normalize catalog SQL without relying on PostgreSQL pretty-print layout."""
    return re.sub(r"\s+", "", value).lower()


def canonical_expression(value: str | None) -> str:
    """Normalize a trigger condition while preserving its operators and names."""
    if value is None:
        return ""
    return canonical_sql(value).replace("(", "").replace(")", "")


def table_exists(connection: psycopg.Connection[Any], table: str) -> bool:
    return bool(scalar(connection, "SELECT to_regclass(%s) IS NOT NULL", (f"public.{table}",)))


def legacy_columns(connection: psycopg.Connection[Any], table: str) -> tuple[str, ...]:
    """Return source columns, excluding only fixed migration additions."""
    column_rows = rows(
        connection,
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = %s ORDER BY ordinal_position",
        (table,),
    )
    columns = tuple(row[0] for row in column_rows if row[0] not in EXPECTED_NEW_COLUMNS[table])
    if not columns or "id" not in columns or (table in TABLES and "created_at" not in columns):
        raise PreflightError("preflight_schema_error")
    return columns


def integrity_snapshot(connection: psycopg.Connection[Any]) -> dict[str, dict[str, Any]]:
    """Hash every legacy value, including relationships and approval-audit records."""
    snapshot: dict[str, dict[str, Any]] = {}
    for table in INTEGRITY_TABLES:
        if not table_exists(connection, table):
            raise PreflightError("preflight_schema_error")
        columns = legacy_columns(connection, table)
        quoted_columns = ", ".join(f'"{column}"' for column in columns)
        table_rows = rows(connection, f"SELECT {quoted_columns} FROM public.{table} ORDER BY id")
        digest = hashlib.sha256()
        for row in table_rows:
            canonical = json.dumps(
                [normalize(value) for value in row], separators=(",", ":"), ensure_ascii=True
            ).encode("utf-8")
            digest.update(len(canonical).to_bytes(8, "big"))
            digest.update(canonical)
        snapshot[table] = {
            "columns": columns,
            "row_count": len(table_rows),
            "sha256": digest.hexdigest(),
        }
    return snapshot


def exact_constraint(
    connection: psycopg.Connection[Any],
    table: str,
    name: str,
    constraint_type: str,
    columns: tuple[str, ...],
    referenced_table: str | None = None,
    referenced_columns: tuple[str, ...] | None = None,
    delete_action: str | None = None,
) -> bool:
    """Verify a named constraint's relation, type, columns, and key properties."""
    result = scalar(
        connection,
        "SELECT c.contype = %s AND c.convalidated AND NOT c.condeferrable "
        "AND (SELECT array_agg(a.attname::text ORDER BY k.ordinality) "
        "FROM unnest(c.conkey) WITH ORDINALITY AS k(attnum, ordinality) "
        "JOIN pg_attribute AS a ON a.attrelid = c.conrelid AND a.attnum = k.attnum) = %s::text[] "
        "AND (%s::regclass IS NULL OR c.confrelid = %s::regclass) "
        "AND (%s::text[] IS NULL OR (SELECT array_agg(a.attname::text ORDER BY k.ordinality) "
        "FROM unnest(c.confkey) WITH ORDINALITY AS k(attnum, ordinality) "
        "JOIN pg_attribute AS a ON a.attrelid = c.confrelid AND a.attnum = k.attnum) = %s::text[]) "
        "AND (%s::text IS NULL OR c.confdeltype = %s::\"char\") "
        "FROM pg_constraint AS c WHERE c.conname = %s AND c.conrelid = %s::regclass",
        (
            constraint_type,
            list(columns),
            referenced_table,
            referenced_table,
            list(referenced_columns) if referenced_columns else None,
            list(referenced_columns) if referenced_columns else None,
            delete_action,
            delete_action,
            name,
            f"public.{table}",
        ),
    )
    return result is True


def sequence_properties(connection: psycopg.Connection[Any], sequence: str) -> tuple[bool, int, bool, int]:
    """Read the fixed migration sequence properties without changing its state."""
    result = rows(
        connection,
        "SELECT c.relkind = 'S', s.seqtypid = 'int8'::regtype, s.seqstart, s.seqincrement, "
        "s.seqmin, s.seqmax, s.seqcache, s.seqcycle "
        "FROM pg_class AS c JOIN pg_sequence AS s ON s.seqrelid = c.oid "
        "WHERE c.oid = %s::regclass",
        (f"public.{sequence}",),
    )
    if len(result) != 1:
        return False, 0, False, 0
    state = rows(connection, f"SELECT last_value, is_called FROM public.{sequence}")
    if len(state) != 1:
        return False, 0, False, 0
    relkind, type_ok, start, increment, minimum, maximum, cache, cycle = result[0]
    last_value, is_called = state[0]
    properties_ok = (
        relkind is True
        and type_ok is True
        and start == 1
        and increment == 1
        and minimum == 1
        and maximum == SEQUENCE_MAXIMUM
        and cache == 1
        and cycle is False
    )
    return properties_ok, int(last_value), bool(is_called), int(increment)


def function_details(
    connection: psycopg.Connection[Any], function_oid: int, expected_name: str, table: str,
    *, requires_hardening: bool,
) -> tuple[bool, str, str] | None:
    """Verify trigger signature metadata and retrieve its catalog definition."""
    result = rows(
        connection,
        "SELECT n.nspname = 'public', p.proname = %s, p.pronargs = 0, p.prorettype = 'trigger'::regtype, "
        "l.lanname = 'plpgsql', NOT p.prosecdef, p.proconfig = ARRAY['search_path=pg_catalog'], "
        "p.proowner = table_relation.relowner, p.prosrc, pg_get_functiondef(p.oid) "
        "FROM pg_proc AS p JOIN pg_namespace AS n ON n.oid = p.pronamespace "
        "JOIN pg_language AS l ON l.oid = p.prolang "
        "JOIN pg_class AS table_relation ON table_relation.oid = %s::regclass WHERE p.oid = %s",
        (expected_name, f"public.{table}", function_oid),
    )
    if len(result) != 1:
        return None
    namespace_ok, name_ok, arguments_ok, return_ok, language_ok, invoker_ok, search_path_ok, owner_ok, source, definition = result[0]
    signature_ok = bool(namespace_ok and name_ok and arguments_ok and return_ok and language_ok and owner_ok)
    return bool(signature_ok and (not requires_hardening or (invoker_ok and search_path_ok))), source, definition


def function_body_matches(source: str, definition: str, expected_body: str) -> bool:
    """Require exact stored source and corroborate it through pg_get_functiondef()."""
    expected = canonical_sql(expected_body)
    return canonical_sql(source) == expected and expected in canonical_sql(definition)


def trigger_details(
    connection: psycopg.Connection[Any], table: str, trigger_name: str
) -> tuple[bool, int, int, str | None] | None:
    """Read structural trigger properties without deparser-format regexes."""
    result = rows(
        connection,
        "SELECT t.tgenabled = 'O', NOT t.tgisinternal, t.tgtype, t.tgfoid, "
        "pg_get_expr(t.tgqual, t.tgrelid) FROM pg_trigger AS t "
        "WHERE t.tgname = %s AND t.tgrelid = %s::regclass",
        (trigger_name, f"public.{table}"),
    )
    if len(result) != 1:
        return None
    enabled, external, trigger_type, function_oid, condition = result[0]
    return bool(enabled and external), int(trigger_type), int(function_oid), condition


def record_number_schema(
    connection: psycopg.Connection[Any], table: str, prefix: str, sequence: str, writer_role: str
) -> dict[str, bool]:
    """Verify exact catalog objects and function bodies created by the migration."""
    column_ok = scalar(
        connection,
        "SELECT a.attnotnull AND t.typname = 'varchar' AND a.atttypmod = 36 "
        "FROM pg_attribute AS a JOIN pg_type AS t ON t.oid = a.atttypid "
        "WHERE a.attrelid = %s::regclass AND a.attname = 'record_number' "
        "AND NOT a.attisdropped",
        (f"public.{table}",),
    ) is True
    sequence_ok, _, _, _ = sequence_properties(connection, sequence)
    writer_role_ok = scalar(
        "SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = %s AND NOT rolsuper)",
        (writer_role,),
    ) is True
    ownership_and_permissions_ok = writer_role_ok and scalar(
        "SELECT sequence_relation.relowner = table_relation.relowner "
        "AND has_table_privilege(%s, table_relation.oid, 'INSERT') "
        "AND has_sequence_privilege(%s, sequence_relation.oid, 'USAGE') "
        "FROM pg_class AS table_relation JOIN pg_class AS sequence_relation ON sequence_relation.oid = %s::regclass "
        "WHERE table_relation.oid = %s::regclass",
        (writer_role, writer_role, f"public.{sequence}", f"public.{table}"),
    ) is True
    unique_ok = exact_constraint(connection, table, f"uq_{table}_record_number", "u", ("record_number",))

    assignment = trigger_details(connection, table, f"trg_assign_{table}_record_number")
    assignment_trigger_ok = assignment is not None and assignment[0] and assignment[1] == 7 and assignment[3] is None
    assignment_function_ok = False
    if assignment is not None:
        details = function_details(
            connection, assignment[2], f"assign_{table}_record_number", table, requires_hardening=True
        )
        assignment_function_ok = details is not None and details[0] and function_body_matches(
            details[1], details[2], HARDENED_ASSIGNMENT_BODY.format(prefix=prefix, sequence=sequence)
        )

    immutable = trigger_details(connection, table, f"trg_prevent_{table}_record_number_change")
    immutable_trigger_ok = (
        immutable is not None
        and immutable[0]
        and immutable[1] == 19
        and canonical_expression(immutable[3]) == "old.record_numberisdistinctfromnew.record_number"
    )
    immutable_function_ok = False
    if immutable is not None:
        details = function_details(
            connection, immutable[2], "prevent_record_number_change", table, requires_hardening=False
        )
        immutable_function_ok = details is not None and details[0] and function_body_matches(
            details[1], details[2], IMMUTABILITY_BODY
        )
    return {
        "column": column_ok,
        "sequence": sequence_ok,
        "ownership_and_writer_permissions": ownership_and_permissions_ok,
        "unique_constraint": unique_ok,
        "assign_trigger": assignment_trigger_ok,
        "assign_function": assignment_function_ok,
        "immutable_trigger": immutable_trigger_ok,
        "immutable_function": immutable_function_ok,
    }


def creator_schema(connection: psycopg.Connection[Any], table: str) -> dict[str, bool]:
    """Verify nullable creator links, exact index, and SET NULL foreign key."""
    column_ok = scalar(
        connection,
        "SELECT NOT a.attnotnull AND t.typname = 'uuid' FROM pg_attribute AS a "
        "JOIN pg_type AS t ON t.oid = a.atttypid WHERE a.attrelid = %s::regclass "
        "AND a.attname = 'created_by_id' AND NOT a.attisdropped",
        (f"public.{table}",),
    ) is True
    index_ok = scalar(
        connection,
        "SELECT NOT i.indisunique AND i.indisvalid "
        "AND (SELECT array_agg(a.attname::text ORDER BY k.ordinality) "
        "FROM unnest(i.indkey) WITH ORDINALITY AS k(attnum, ordinality) "
        "JOIN pg_attribute AS a ON a.attrelid = i.indrelid AND a.attnum = k.attnum) "
        "= ARRAY['created_by_id'] FROM pg_index AS i JOIN pg_class AS c ON c.oid = i.indexrelid "
        "WHERE c.relname = %s AND i.indrelid = %s::regclass",
        (f"ix_{table}_created_by_id", f"public.{table}"),
    ) is True
    foreign_key_ok = exact_constraint(
        connection,
        table,
        f"fk_{table}_created_by_id_users",
        "f",
        ("created_by_id",),
        "public.users",
        ("id",),
        "n",
    )
    return {"column": column_ok, "index": index_ok, "foreign_key": foreign_key_ok}


def record_number_values(
    connection: psycopg.Connection[Any], table: str, prefix: str, sequence: str
) -> dict[str, bool]:
    """Verify values and effective next sequence value without advancing it."""
    values = rows(
        connection,
        f"SELECT id, created_at, record_number FROM public.{table} ORDER BY created_at, id",
    )
    expected = [f"{prefix}-{position:03d}" for position in range(1, len(values) + 1)]
    assigned = [row[2] for row in values]
    pattern = re.compile(rf"^{re.escape(prefix)}-[0-9]{{3,}}$")
    suffixes = [
        int(value.rsplit("-", 1)[1])
        for value in assigned
        if isinstance(value, str) and pattern.fullmatch(value)
    ]
    sequence_ok, last_value, is_called, increment = sequence_properties(connection, sequence)
    effective_next = last_value + (increment if is_called else 0)
    return {
        "prefix": len(assigned) == len(suffixes),
        "non_null": all(value is not None for value in assigned),
        "unique": len(assigned) == len(set(assigned)),
        "deterministic_order": assigned == expected,
        "sequence_properties": sequence_ok,
        "sequence_aligned": effective_next > max(suffixes, default=0)
        and effective_next <= SEQUENCE_MAXIMUM,
    }


def revisions(connection: psycopg.Connection[Any]) -> tuple[str, ...]:
    return tuple(row[0] for row in rows(connection, "SELECT version_num FROM alembic_version ORDER BY version_num"))


def migration_prerequisites() -> dict[str, bool]:
    """Verify the reviewed migration chain and hardened follow-up on disk."""
    verified: list[tuple[str, str, str]] = []
    files_verified = True
    for filename, revision, down_revision, expected_digest in EXPECTED_MIGRATION_CHAIN:
        path = MIGRATIONS_DIRECTORY / filename
        try:
            source = path.read_bytes()
            text = source.decode("utf-8", errors="strict")
        except (OSError, UnicodeDecodeError):
            files_verified = False
            continue
        revision_match = REVISION_ASSIGNMENT.search(text)
        down_revision_match = DOWN_REVISION_ASSIGNMENT.search(text)
        if (
            hashlib.sha256(source).hexdigest() != expected_digest
            or revision_match is None
            or down_revision_match is None
            or revision_match.group(1) != revision
            or down_revision_match.group(1) != down_revision
        ):
            files_verified = False
            continue
        verified.append((filename, revision, down_revision))
    chain_verified = (
        files_verified
        and len(verified) == len(EXPECTED_MIGRATION_CHAIN)
        and all(verified[index][2] == verified[index - 1][1] for index in range(1, len(verified)))
        and verified[-1][1] == "d4e5f6a7b8c9"
    )
    followup_path = MIGRATIONS_DIRECTORY / EXPECTED_MIGRATION_CHAIN[-1][0]
    try:
        followup_text = followup_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        followup_text = ""
    followup_intent_verified = chain_verified and all(
        fragment in followup_text for fragment in SECURITY_FOLLOWUP_FRAGMENTS
    )
    result = {
        "source_revision_file": files_verified and bool(verified) and verified[0][1] == EXPECTED_SOURCE_REVISION,
        "target_migration_file": files_verified and len(verified) > 2 and verified[2][1] == TARGET_REVISION,
        "security_followup_file": files_verified and len(verified) > 2 and verified[2][1] == "d4e5f6a7b8c9",
        "revision_chain_to_security_followup": chain_verified,
        "security_followup_intent": followup_intent_verified,
    }
    if not all(result.values()):
        raise PreflightError("migration_prerequisite_failed")
    return result


def migration_file_hashes() -> dict[str, str]:
    """Return only reviewed migration filenames and their fixed SHA-256 values."""
    return {filename: digest for filename, _, _, digest in EXPECTED_MIGRATION_CHAIN}


def approval_binding_sha256(
    container_id: str, run_id: str, baseline: dict[str, dict[str, Any]]
) -> str:
    """Hash the immutable approval evidence without exposing its container ID."""
    binding = {
        "database_identity": {
            "host": EXPECTED_ENDPOINT[0],
            "name": EXPECTED_ENDPOINT[2],
            "port": int(EXPECTED_ENDPOINT[1]),
        },
        "migration_file_hashes": migration_file_hashes(),
        "restore_container_id": container_id,
        "run_id": run_id,
        "source_revision": EXPECTED_SOURCE_REVISION,
        "baseline": baseline,
    }
    return hashlib.sha256(
        json.dumps(binding, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def approval_record(
    container_id: str, baseline: dict[str, dict[str, Any]]
) -> dict[str, str | int]:
    """Create a nonce-bound approval request, never an authorization."""
    run_id = hashlib.sha256(os.urandom(32)).hexdigest()
    binding_sha256 = approval_binding_sha256(container_id, run_id, baseline)
    return {
        "binding_sha256": binding_sha256,
        "restore_container_id_sha256": hashlib.sha256(container_id.encode("ascii")).hexdigest(),
        "run_id": run_id,
        "version": 1,
    }


def preflight_report(
    connection: psycopg.Connection[Any], prerequisites: dict[str, bool], container_id: str
) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
    """Validate endpoint and source revision before any migration invocation."""
    identity = bool(
        scalar(
            connection,
            "SELECT current_database() = %s AND inet_server_addr() = %s::inet "
            "AND inet_server_port() = %s",
            (EXPECTED_ENDPOINT[2], EXPECTED_ENDPOINT[0], int(EXPECTED_ENDPOINT[1])),
        )
    )
    source_revision = revisions(connection) == (EXPECTED_SOURCE_REVISION,)
    tables = {table: table_exists(connection, table) for table in INTEGRITY_TABLES}
    if not identity or not source_revision or not all(tables.values()):
        raise PreflightError("preflight_validation_failed")
    snapshot = integrity_snapshot(connection)
    return {
        "approval": approval_record(container_id, snapshot),
        "database_identity": {
            "host": EXPECTED_ENDPOINT[0],
            "name": EXPECTED_ENDPOINT[2],
            "port": int(EXPECTED_ENDPOINT[1]),
        },
        "migration_file_hashes": migration_file_hashes(),
        "phase": "preflight",
        "report_type": "migration_rehearsal_preflight",
        "report_version": 1,
        "target_identity_verified": identity,
        "source_revision_verified": source_revision,
        "source_revision": EXPECTED_SOURCE_REVISION,
        "migration_prerequisites": prerequisites,
        "tables": tables,
        "integrity": snapshot,
    }, snapshot


def load_preflight_report() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """Load and validate the fixed preflight report without querying PostgreSQL."""
    try:
        report = json.loads(PREFLIGHT_REPORT_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise PostflightError("preflight_report_error") from error
    if (
        not isinstance(report, dict)
        or report.get("phase") != "preflight"
        or report.get("report_type") != "migration_rehearsal_preflight"
        or report.get("report_version") != 1
        or report.get("database_identity")
        != {
            "host": EXPECTED_ENDPOINT[0],
            "name": EXPECTED_ENDPOINT[2],
            "port": int(EXPECTED_ENDPOINT[1]),
        }
        or report.get("source_revision") != EXPECTED_SOURCE_REVISION
        or report.get("migration_file_hashes") != migration_file_hashes()
    ):
        raise PostflightError("preflight_report_error")
    approval = report.get("approval")
    if not isinstance(approval, dict) or set(approval) != {
        "binding_sha256", "restore_container_id_sha256", "run_id", "version"
    }:
        raise PostflightError("preflight_report_error")
    tables = report.get("tables")
    prerequisites = report.get("migration_prerequisites")
    if (
        report.get("target_identity_verified") is not True
        or report.get("source_revision_verified") is not True
        or not isinstance(prerequisites, dict)
        or set(prerequisites)
        != {
            "source_revision_file",
            "target_migration_file",
            "security_followup_file",
            "revision_chain_to_security_followup",
            "security_followup_intent",
        }
        or any(value is not True for value in prerequisites.values())
        or not isinstance(tables, dict)
        or set(tables) != set(INTEGRITY_TABLES)
        or any(value is not True for value in tables.values())
    ):
        raise PostflightError("preflight_report_error")
    integrity = report.get("integrity")
    if not isinstance(integrity, dict) or set(integrity) != set(INTEGRITY_TABLES):
        raise PostflightError("preflight_report_error")
    baseline: dict[str, dict[str, Any]] = {}
    for table in INTEGRITY_TABLES:
        entry = integrity[table]
        if not isinstance(entry, dict) or set(entry) != {"columns", "row_count", "sha256"}:
            raise PostflightError("preflight_report_error")
        columns = entry["columns"]
        row_count = entry["row_count"]
        digest = entry["sha256"]
        if (
            not isinstance(columns, list)
            or not all(isinstance(column, str) for column in columns)
            or isinstance(row_count, bool)
            or not isinstance(row_count, int)
            or row_count < 0
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            raise PostflightError("preflight_report_error")
        baseline[table] = {"columns": tuple(columns), "row_count": row_count, "sha256": digest}
    run_id = approval["run_id"]
    binding_sha256 = approval["binding_sha256"]
    restore_id_sha256 = approval["restore_container_id_sha256"]
    container_id = restore_container_id()
    if (
        approval["version"] != 1
        or not isinstance(run_id, str)
        or re.fullmatch(r"[0-9a-f]{64}", run_id) is None
        or not isinstance(binding_sha256, str)
        or not isinstance(restore_id_sha256, str)
        or binding_sha256 != approval_binding_sha256(container_id, run_id, baseline)
        or restore_id_sha256 != hashlib.sha256(container_id.encode("ascii")).hexdigest()
    ):
        raise PostflightError("preflight_report_error")
    return baseline, approval


def record_number_writer_role() -> str:
    """Require the reviewed, non-superuser role expected to insert records."""
    role = required("REHEARSAL_RECORD_NUMBER_WRITER_ROLE")
    if scalar_role_name(role) is None:
        raise PostflightError("writer_role_configuration_error")
    return role


def scalar_role_name(role: str) -> str | None:
    """Validate a role name without interpolating it into SQL."""
    if not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", role):
        return None
    return role


def verify_external_approval(approval: dict[str, Any]) -> None:
    """Refuse upgrades until a separately trusted approval verifier is provisioned.

    A bound report digest proves only that data is consistent; it does not prove
    a human authorized the change. This image deliberately contains no signing
    verifier or trusted public key, so accepting a file, token, or digest here
    would let the helper authorize itself.
    """
    del approval
    raise RehearsalError("approval_verifier_unavailable")


def alembic_identity_environment(connection: psycopg.Connection[Any]) -> dict[str, str]:
    """Capture immutable cluster and database identifiers for Alembic's new connection."""
    result = rows(
        connection,
        "SELECT current_database(), (SELECT oid FROM pg_database WHERE datname = current_database()), "
        "(pg_control_system()).system_identifier::text",
    )
    if len(result) != 1:
        raise PreflightError("migration_identity_unavailable")
    database_name, database_oid, system_identifier = result[0]
    if (
        database_name != EXPECTED_ENDPOINT[2]
        or not isinstance(database_oid, int)
        or database_oid <= 0
        or not isinstance(system_identifier, str)
        or re.fullmatch(r"[1-9][0-9]{0,19}", system_identifier) is None
    ):
        raise PreflightError("migration_identity_unavailable")
    return {
        "REHEARSAL_EXPECTED_DATABASE_OID": str(database_oid),
        "REHEARSAL_EXPECTED_SYSTEM_IDENTIFIER": system_identifier,
    }


def postflight_report(
    connection: psycopg.Connection[Any], baseline: dict[str, dict[str, Any]], writer_role: str
) -> dict[str, Any]:
    """Verify every required migrated object and preservation invariant."""
    identity = bool(
        scalar(
            connection,
            "SELECT current_database() = %s AND inet_server_addr() = %s::inet "
            "AND inet_server_port() = %s",
            (EXPECTED_ENDPOINT[2], EXPECTED_ENDPOINT[0], int(EXPECTED_ENDPOINT[1])),
        )
    )
    current = integrity_snapshot(connection)
    integrity = {
        table: current[table]["columns"] == baseline[table]["columns"]
        and current[table]["row_count"] == baseline[table]["row_count"]
        and current[table]["sha256"] == baseline[table]["sha256"]
        for table in INTEGRITY_TABLES
    }
    schema = {
        table: record_number_schema(connection, table, prefix, sequence, writer_role)
        for table, prefix, sequence in RECORD_NUMBER_CONFIG
    }
    values = {
        table: record_number_values(connection, table, prefix, sequence)
        for table, prefix, sequence in RECORD_NUMBER_CONFIG
    }
    creators = {table: creator_schema(connection, table) for table in CREATOR_TABLES}
    target_revision = revisions(connection) == (TARGET_REVISION,)
    passed = (
        identity
        and target_revision
        and all(integrity.values())
        and all(all(checks.values()) for checks in schema.values())
        and all(all(checks.values()) for checks in values.values())
        and all(all(checks.values()) for checks in creators.values())
    )
    return {
        "phase": "postflight",
        "target_identity_verified": identity,
        "target_revision_verified": target_revision,
        "integrity": integrity,
        "record_number_schema": schema,
        "record_number_values": values,
        "creator_schema": creators,
        "passed": passed,
    }


def stage() -> str:
    """Require one explicit, mutually exclusive rehearsal stage."""
    if len(sys.argv) != 2 or sys.argv[1] not in {"preflight", "upgrade"}:
        raise ConfigurationError("configuration_error")
    return sys.argv[1]


def run_preflight() -> None:
    """Stage A: run only read-only database validation and emit its baseline."""
    prerequisites = migration_prerequisites()
    container_id = restore_container_id()
    with psycopg.connect(**connection_kwargs(read_only=True), autocommit=True) as connection:
        preflight, _ = preflight_report(connection, prerequisites, container_id)
    print(json.dumps(preflight, sort_keys=True))


def run_upgrade() -> None:
    """Stage C: revalidate an external approval before the fixed upgrade."""
    baseline, approval = load_preflight_report()
    verify_external_approval(approval)
    with psycopg.connect(**connection_kwargs(read_only=True), autocommit=True) as connection:
        _, current_baseline = preflight_report(
            connection, migration_prerequisites(), restore_container_id()
        )
    if current_baseline != baseline:
        raise RehearsalError("approval_stale_or_target_drift")
    writer_role = record_number_writer_role()
    with psycopg.connect(**connection_kwargs(read_only=True), autocommit=True) as connection:
        identity_environment = alembic_identity_environment(connection)
    child_environment = {
        name: required(name)
        for name in (
            "REHEARSAL_DATABASE_HOST",
            "REHEARSAL_DATABASE_PORT",
            "REHEARSAL_DATABASE_NAME",
            "REHEARSAL_DATABASE_USER",
        )
    }
    child_environment["REHEARSAL_RECORD_NUMBER_WRITER_ROLE"] = writer_role
    child_environment.update(identity_environment)
    child_environment["PATH"] = "/workspace/backend/.venv/bin:/usr/bin:/bin"
    completed = subprocess.run(
        ["alembic", "-c", ALEMBIC_CONFIG, "upgrade", TARGET_REVISION],
        check=False,
        env=child_environment,
        capture_output=True,
    )
    if completed.returncode != 0:
        raise RehearsalError("migration_process_failed")


    with psycopg.connect(**connection_kwargs(read_only=True), autocommit=True) as connection:
        postflight = postflight_report(connection, baseline, writer_role)
    print(json.dumps(postflight, sort_keys=True))
    if not postflight["passed"]:
        raise PostflightError("postflight_validation_failed")


def main() -> int:
    """Run exactly one explicit stage; validation stages cannot execute Alembic."""
    try:
        selected_stage = stage()
        if selected_stage == "preflight":
            run_preflight()
        elif selected_stage == "upgrade":
            run_upgrade()
        else:
            raise ConfigurationError("configuration_error")
        return 0
    except ConfigurationError as error:
        print(f"rehearsal refused: {error}", file=sys.stderr)
    except PreflightError as error:
        print(f"rehearsal refused: {error}", file=sys.stderr)
    except PostflightError as error:
        print(f"rehearsal failed: {error}", file=sys.stderr)
    except CanonicalizationError as error:
        print(f"rehearsal failed: {error}", file=sys.stderr)
    except RehearsalError as error:
        print(f"rehearsal failed: {error}", file=sys.stderr)
    except subprocess.SubprocessError:
        print("rehearsal failed: migration_process_failed", file=sys.stderr)
    except (OSError, psycopg.Error):
        print("rehearsal failed: database_or_runtime_error", file=sys.stderr)
    except Exception:
        print("rehearsal failed: unexpected_error", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
