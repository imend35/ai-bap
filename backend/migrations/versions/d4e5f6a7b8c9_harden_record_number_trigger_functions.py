"""Harden record-number trigger functions against search-path hijacking.

Revision ID: d4e5f6a7b8c9
Revises: c7a8d9e0f1b2

PostgreSQL runs Alembic revisions transactionally.  SET LOCAL therefore keeps
the lock timeout scoped to this revision transaction.  CREATE OR REPLACE keeps
the existing function owners, so the migration role must own the four existing
functions (or otherwise be permitted to replace them).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "d4e5f6a7b8c9"
down_revision: str | Sequence[str] | None = "c7a8d9e0f1b2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Replace only the four trigger functions with fixed search paths."""
    op.execute(sa.text("SET LOCAL lock_timeout = '5s'"))
    op.execute(
        sa.text(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_catalog.pg_class AS sequence_relation
                    JOIN pg_catalog.pg_namespace AS sequence_schema
                        ON sequence_schema.oid = sequence_relation.relnamespace
                    WHERE sequence_schema.nspname = 'public'
                        AND sequence_relation.relname = 'users_record_number_seq'
                        AND sequence_relation.relkind = 'S'
                ) THEN
                    RAISE EXCEPTION 'required public.users_record_number_seq is not a sequence';
                END IF;
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_catalog.pg_class AS sequence_relation
                    JOIN pg_catalog.pg_namespace AS sequence_schema
                        ON sequence_schema.oid = sequence_relation.relnamespace
                    WHERE sequence_schema.nspname = 'public'
                        AND sequence_relation.relname = 'projects_record_number_seq'
                        AND sequence_relation.relkind = 'S'
                ) THEN
                    RAISE EXCEPTION 'required public.projects_record_number_seq is not a sequence';
                END IF;
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_catalog.pg_class AS sequence_relation
                    JOIN pg_catalog.pg_namespace AS sequence_schema
                        ON sequence_schema.oid = sequence_relation.relnamespace
                    WHERE sequence_schema.nspname = 'public'
                        AND sequence_relation.relname = 'requirements_record_number_seq'
                        AND sequence_relation.relkind = 'S'
                ) THEN
                    RAISE EXCEPTION 'required public.requirements_record_number_seq is not a sequence';
                END IF;
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_catalog.pg_class AS sequence_relation
                    JOIN pg_catalog.pg_namespace AS sequence_schema
                        ON sequence_schema.oid = sequence_relation.relnamespace
                    WHERE sequence_schema.nspname = 'public'
                        AND sequence_relation.relname = 'user_stories_record_number_seq'
                        AND sequence_relation.relkind = 'S'
                ) THEN
                    RAISE EXCEPTION 'required public.user_stories_record_number_seq is not a sequence';
                END IF;

                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_catalog.pg_trigger AS assignment_trigger
                    WHERE assignment_trigger.tgname = 'trg_assign_users_record_number'
                        AND assignment_trigger.tgrelid = 'public.users'::pg_catalog.regclass
                        AND assignment_trigger.tgfoid =
                            'public.assign_users_record_number()'::pg_catalog.regprocedure
                        AND assignment_trigger.tgtype = 7
                        AND assignment_trigger.tgenabled = 'O'
                        AND NOT assignment_trigger.tgisinternal
                ) THEN
                    RAISE EXCEPTION 'users record-number assignment trigger is missing or drifted';
                END IF;
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_catalog.pg_trigger AS assignment_trigger
                    WHERE assignment_trigger.tgname = 'trg_assign_projects_record_number'
                        AND assignment_trigger.tgrelid = 'public.projects'::pg_catalog.regclass
                        AND assignment_trigger.tgfoid =
                            'public.assign_projects_record_number()'::pg_catalog.regprocedure
                        AND assignment_trigger.tgtype = 7
                        AND assignment_trigger.tgenabled = 'O'
                        AND NOT assignment_trigger.tgisinternal
                ) THEN
                    RAISE EXCEPTION 'projects record-number assignment trigger is missing or drifted';
                END IF;
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_catalog.pg_trigger AS assignment_trigger
                    WHERE assignment_trigger.tgname = 'trg_assign_requirements_record_number'
                        AND assignment_trigger.tgrelid = 'public.requirements'::pg_catalog.regclass
                        AND assignment_trigger.tgfoid =
                            'public.assign_requirements_record_number()'::pg_catalog.regprocedure
                        AND assignment_trigger.tgtype = 7
                        AND assignment_trigger.tgenabled = 'O'
                        AND NOT assignment_trigger.tgisinternal
                ) THEN
                    RAISE EXCEPTION 'requirements record-number assignment trigger is missing or drifted';
                END IF;
                IF NOT EXISTS (
                    SELECT 1
                    FROM pg_catalog.pg_trigger AS assignment_trigger
                    WHERE assignment_trigger.tgname = 'trg_assign_user_stories_record_number'
                        AND assignment_trigger.tgrelid = 'public.user_stories'::pg_catalog.regclass
                        AND assignment_trigger.tgfoid =
                            'public.assign_user_stories_record_number()'::pg_catalog.regprocedure
                        AND assignment_trigger.tgtype = 7
                        AND assignment_trigger.tgenabled = 'O'
                        AND NOT assignment_trigger.tgisinternal
                ) THEN
                    RAISE EXCEPTION 'user_stories record-number assignment trigger is missing or drifted';
                END IF;
            END;
            $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION public.assign_users_record_number()
            RETURNS trigger
            LANGUAGE plpgsql
            SET search_path = pg_catalog
            AS $$
            BEGIN
                IF NEW.record_number IS NOT NULL THEN
                    RAISE EXCEPTION 'record_number is assigned by PostgreSQL';
                END IF;
                NEW.record_number := 'USR-' || pg_catalog.lpad(
                    pg_catalog.nextval('public.users_record_number_seq'::pg_catalog.regclass)::text,
                    3,
                    '0'
                );
                RETURN NEW;
            END;
            $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION public.assign_projects_record_number()
            RETURNS trigger
            LANGUAGE plpgsql
            SET search_path = pg_catalog
            AS $$
            BEGIN
                IF NEW.record_number IS NOT NULL THEN
                    RAISE EXCEPTION 'record_number is assigned by PostgreSQL';
                END IF;
                NEW.record_number := 'PRJ-' || pg_catalog.lpad(
                    pg_catalog.nextval('public.projects_record_number_seq'::pg_catalog.regclass)::text,
                    3,
                    '0'
                );
                RETURN NEW;
            END;
            $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION public.assign_requirements_record_number()
            RETURNS trigger
            LANGUAGE plpgsql
            SET search_path = pg_catalog
            AS $$
            BEGIN
                IF NEW.record_number IS NOT NULL THEN
                    RAISE EXCEPTION 'record_number is assigned by PostgreSQL';
                END IF;
                NEW.record_number := 'REQ-' || pg_catalog.lpad(
                    pg_catalog.nextval('public.requirements_record_number_seq'::pg_catalog.regclass)::text,
                    3,
                    '0'
                );
                RETURN NEW;
            END;
            $$;
            """
        )
    )
    op.execute(
        sa.text(
            """
            CREATE OR REPLACE FUNCTION public.assign_user_stories_record_number()
            RETURNS trigger
            LANGUAGE plpgsql
            SET search_path = pg_catalog
            AS $$
            BEGIN
                IF NEW.record_number IS NOT NULL THEN
                    RAISE EXCEPTION 'record_number is assigned by PostgreSQL';
                END IF;
                NEW.record_number := 'US-' || pg_catalog.lpad(
                    pg_catalog.nextval('public.user_stories_record_number_seq'::pg_catalog.regclass)::text,
                    3,
                    '0'
                );
                RETURN NEW;
            END;
            $$;
            """
        )
    )


def downgrade() -> None:
    """Refuse a downgrade that would reintroduce vulnerable definitions."""
    raise NotImplementedError(
        "Downgrade of record-number trigger-function hardening is intentionally unsupported."
    )
