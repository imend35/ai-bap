"""Static regression checks for record-number formatting beyond three digits."""

from pathlib import Path

import pytest

MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "c8d9e0f1a2b3_correct_record_number_greatest_syntax.py"
)
RECORD_NUMBER_CONFIG = (
    ("users", "USR", "users_record_number_seq"),
    ("projects", "PRJ", "projects_record_number_seq"),
    ("requirements", "REQ", "requirements_record_number_seq"),
    ("user_stories", "US", "user_stories_record_number_seq"),
)


def expected_record_number(prefix: str, value: int) -> str:
    """I model the migration's minimum-width formatting contract."""
    number_text = str(value)
    return f"{prefix}-{number_text.zfill(max(len(number_text), 3))}"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (9, "USR-009"),
        (112, "USR-112"),
        (999, "USR-999"),
        (1000, "USR-1000"),
        (1122, "USR-1122"),
    ],
)
def test_record_number_formatting_retains_digits_above_minimum_width(
    value: int,
    expected: str,
) -> None:
    """I preserve every sequence digit while padding values below one hundred."""
    assert expected_record_number("USR", value) == expected


def test_migration_replaces_every_generator_with_minimum_width_padding() -> None:
    """I keep all record-number trigger functions non-truncating and secure."""
    source = MIGRATION.read_text(encoding="utf-8")

    assert 'revision: str = "c8d9e0f1a2b3"' in source
    assert 'down_revision: str | Sequence[str] | None = "b6c7d8e9f0a1"' in source
    assert source.count("CREATE OR REPLACE FUNCTION public.assign_") == 1
    assert "for table_name, prefix, sequence_name in RECORD_NUMBER_CONFIG:" in source
    assert "CREATE OR REPLACE FUNCTION public.assign_{table_name}_record_number()" in source
    assert "number_text text;" in source
    assert "GREATEST(pg_catalog.length(number_text), 3)" in source
    assert "pg_catalog.greatest(" not in source
    assert "SET search_path = pg_catalog" in source
    assert "IF NEW.record_number IS NOT NULL THEN" in source
    assert "RAISE EXCEPTION 'record_number is assigned by PostgreSQL'" in source
    assert "'public.{sequence_name}'::pg_catalog.regclass" in source
    assert "SETVAL" not in source
    assert "ALTER SEQUENCE" not in source

    for table_name, prefix, sequence_name in RECORD_NUMBER_CONFIG:
        assert f'("{table_name}", "{prefix}", "{sequence_name}")' in source


def test_migration_is_forward_only_and_does_not_rewrite_existing_records() -> None:
    """I avoid sequence resets and existing-record changes in the repair."""
    source = MIGRATION.read_text(encoding="utf-8")

    assert "raise NotImplementedError(" in source
    for prohibited_fragment in (
        "UPDATE ",
        "INSERT INTO",
        "DELETE FROM",
        "DROP ",
        "CREATE SEQUENCE",
        "setval",
        "nextval('public.",
    ):
        assert prohibited_fragment not in source
