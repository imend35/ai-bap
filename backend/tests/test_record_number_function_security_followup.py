"""Static checks for the record-number trigger-function security follow-up."""

import re
from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "d4e5f6a7b8c9_harden_record_number_trigger_functions.py"
)
ORIGINAL_MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "c7a8d9e0f1b2_add_readable_record_numbers_and_creators.py"
)
RECORD_NUMBER_CONFIG = (
    ("users", "USR", "users_record_number_seq"),
    ("projects", "PRJ", "projects_record_number_seq"),
    ("requirements", "REQ", "requirements_record_number_seq"),
    ("user_stories", "US", "user_stories_record_number_seq"),
)


def function_body(source: str, table_name: str) -> str:
    """Extract one replacement function body from the follow-up migration."""
    function_match = re.search(
        rf"CREATE OR REPLACE FUNCTION public\.assign_{table_name}_record_number\(\)"
        r"(?P<body>.*?)\$\$;",
        source,
        flags=re.DOTALL,
    )
    assert function_match is not None
    return function_match.group("body")


def test_security_followup_has_the_expected_revision_chain() -> None:
    """I verify this replacement-only revision follows the record-number revision."""
    source = MIGRATION.read_text(encoding="utf-8")

    assert 'revision: str = "d4e5f6a7b8c9"' in source
    assert 'down_revision: str | Sequence[str] | None = "c7a8d9e0f1b2"' in source


def test_security_followup_replaces_exactly_the_four_trigger_functions() -> None:
    """I compare every replacement with the original generated-function contract."""
    source = MIGRATION.read_text(encoding="utf-8")
    original_source = ORIGINAL_MIGRATION.read_text(encoding="utf-8")

    assert source.count("CREATE OR REPLACE FUNCTION public.assign_") == 4
    assert "CREATE FUNCTION assign_{table_name}_record_number()" in original_source
    assert "IF NEW.record_number IS NOT NULL THEN" in original_source
    assert "RAISE EXCEPTION 'record_number is assigned by PostgreSQL'" in original_source
    assert "LPAD(nextval('{sequence_name}')::text, 3, '0')" in original_source
    assert "RETURN NEW;" in original_source

    for table_name, prefix, sequence_name in RECORD_NUMBER_CONFIG:
        body = function_body(source, table_name)
        assert "RETURNS trigger" in body
        assert "LANGUAGE plpgsql" in body
        assert "SET search_path = pg_catalog" in body
        assert "IF NEW.record_number IS NOT NULL THEN" in body
        assert "RAISE EXCEPTION 'record_number is assigned by PostgreSQL'" in body
        assert f"NEW.record_number := '{prefix}-'" in body
        assert (
            f"pg_catalog.nextval('public.{sequence_name}'::pg_catalog.regclass)::text"
            in body
        )
        assert "pg_catalog.lpad(" in body
        assert "RETURN NEW;" in body


def test_security_followup_validates_sequence_types_and_trigger_bindings_first() -> None:
    """I reject name-only sequence checks and drifted assignment-trigger bindings."""
    source = MIGRATION.read_text(encoding="utf-8")
    preflight = source[source.index("DO $$") : source.index("CREATE OR REPLACE FUNCTION")]

    assert "pg_catalog.to_regclass" not in preflight
    assert "pg_catalog.pg_class AS sequence_relation" in preflight
    assert "pg_catalog.pg_namespace AS sequence_schema" in preflight
    for table_name, _, sequence_name in RECORD_NUMBER_CONFIG:
        assert "sequence_schema.nspname = 'public'" in preflight
        assert f"sequence_relation.relname = '{sequence_name}'" in preflight
        assert "sequence_relation.relkind = 'S'" in preflight
        assert (
            f"assignment_trigger.tgname = 'trg_assign_{table_name}_record_number'"
            in preflight
        )
        assert (
            f"assignment_trigger.tgrelid = 'public.{table_name}'::pg_catalog.regclass"
            in preflight
        )
        assert (
            "assignment_trigger.tgfoid =\n"
            f"                            'public.assign_{table_name}_record_number()'"
            "::pg_catalog.regprocedure"
        ) in preflight
        assert "assignment_trigger.tgtype = 7" in preflight
        assert "assignment_trigger.tgenabled = 'O'" in preflight
        assert "NOT assignment_trigger.tgisinternal" in preflight


def test_original_trigger_template_matches_followup_preflight_associations() -> None:
    """I preserve all four original assignment-trigger table and function associations."""
    original_source = ORIGINAL_MIGRATION.read_text(encoding="utf-8")
    source = MIGRATION.read_text(encoding="utf-8")

    assert "CREATE TRIGGER trg_assign_{table_name}_record_number" in original_source
    assert "BEFORE INSERT ON {table_name}" in original_source
    assert "EXECUTE FUNCTION assign_{table_name}_record_number();" in original_source
    for table_name, _, _ in RECORD_NUMBER_CONFIG:
        assert f"'trg_assign_{table_name}_record_number'" in source
        assert f"'public.{table_name}'::pg_catalog.regclass" in source
        assert f"'public.assign_{table_name}_record_number()'::pg_catalog.regprocedure" in source


def test_security_followup_fails_closed_without_unrelated_database_changes() -> None:
    """I verify prerequisites, timeout, and the intentionally unsupported downgrade."""
    source = MIGRATION.read_text(encoding="utf-8")

    assert "SET LOCAL lock_timeout = '5s'" in source
    assert "raise NotImplementedError(" in source

    for prohibited_pattern in (
        r"\bALTER\s+TABLE\b",
        r"\bCREATE\s+SEQUENCE\b",
        r"\bDROP\b",
        r"\bGRANT\b",
        r"\bREVOKE\b",
        r"\bSECURITY\s+DEFINER\b",
        r"\bUPDATE\b",
        r"\bINSERT\s+INTO\b",
        r"\bDELETE\s+FROM\b",
        r"\bSETVAL\s*\(",
        r"\bCREATE\s+TRIGGER\b",
    ):
        assert re.search(prohibited_pattern, source, flags=re.IGNORECASE) is None
