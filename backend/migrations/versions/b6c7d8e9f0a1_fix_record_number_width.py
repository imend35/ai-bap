"""Fix record-number formatting beyond three digits.

Revision ID: b6c7d8e9f0a1
Revises: e8f1a2b3c4d5

This revision replaces only the four assignment trigger functions. It does not
reset sequences or rewrite existing record numbers.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b6c7d8e9f0a1"
down_revision: str | Sequence[str] | None = "e8f1a2b3c4d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


RECORD_NUMBER_CONFIG = (
    ("users", "USR", "users_record_number_seq"),
    ("projects", "PRJ", "projects_record_number_seq"),
    ("requirements", "REQ", "requirements_record_number_seq"),
    ("user_stories", "US", "user_stories_record_number_seq"),
)


def upgrade() -> None:
    """Keep record-number padding at three digits without truncating larger values."""
    op.execute(sa.text("SET LOCAL lock_timeout = '5s'"))

    for table_name, prefix, sequence_name in RECORD_NUMBER_CONFIG:
        op.execute(
            sa.text(
                f"""
                CREATE OR REPLACE FUNCTION public.assign_{table_name}_record_number()
                RETURNS trigger
                LANGUAGE plpgsql
                SET search_path = pg_catalog
                AS $$
                DECLARE
                    number_text text;
                BEGIN
                    IF NEW.record_number IS NOT NULL THEN
                        RAISE EXCEPTION 'record_number is assigned by PostgreSQL';
                    END IF;
                    number_text := pg_catalog.nextval(
                        'public.{sequence_name}'::pg_catalog.regclass
                    )::text;
                    NEW.record_number := '{prefix}-' || pg_catalog.lpad(
                        number_text,
                        pg_catalog.greatest(pg_catalog.length(number_text), 3),
                        '0'
                    );
                    RETURN NEW;
                END;
                $$;
                """
            )
        )


def downgrade() -> None:
    """Refuse to restore truncating record-number generation."""
    raise NotImplementedError(
        "Downgrade would reintroduce record-number truncation and is unsupported."
    )
