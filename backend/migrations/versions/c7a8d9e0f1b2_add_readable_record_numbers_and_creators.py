"""add readable record numbers and nullable creators

Revision ID: c7a8d9e0f1b2
Revises: 921eeafe8be6
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "c7a8d9e0f1b2"
down_revision: str | Sequence[str] | None = "921eeafe8be6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


RECORD_NUMBER_CONFIG = (
    ("projects", "PRJ", "projects_record_number_seq"),
    ("requirements", "REQ", "requirements_record_number_seq"),
    ("user_stories", "US", "user_stories_record_number_seq"),
    ("users", "USR", "users_record_number_seq"),
)


def upgrade() -> None:
    """Add database-generated record numbers and nullable creator links."""
    # I fail cleanly instead of waiting indefinitely behind active transactions.
    op.execute(
        sa.text(
            "SET LOCAL lock_timeout = '5s'"
        )
    )

    # I prevent writes throughout backfill and sequence alignment while allowing
    # ordinary reads. Individual ALTER TABLE and constraint statements acquire
    # PostgreSQL's stronger, short-lived DDL locks when they execute.
    op.execute(
        sa.text(
            "LOCK TABLE users, projects, requirements, user_stories "
            "IN SHARE ROW EXCLUSIVE MODE"
        )
    )

    for table_name, _, sequence_name in RECORD_NUMBER_CONFIG:
        op.execute(sa.text(f"CREATE SEQUENCE {sequence_name} AS BIGINT START WITH 1"))
        op.add_column(
            table_name,
            sa.Column("record_number", sa.String(length=32), nullable=True),
        )

    for table_name in ("projects", "requirements", "user_stories"):
        op.add_column(
            table_name,
            sa.Column("created_by_id", sa.UUID(), nullable=True),
        )
        op.create_index(
            f"ix_{table_name}_created_by_id",
            table_name,
            ["created_by_id"],
            unique=False,
        )
        op.create_foreign_key(
            f"fk_{table_name}_created_by_id_users",
            table_name,
            "users",
            ["created_by_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        sa.text(
            """
            CREATE FUNCTION prevent_record_number_change()
            RETURNS trigger AS $$
            BEGIN
                RAISE EXCEPTION 'record_number is immutable';
            END;
            $$ LANGUAGE plpgsql;
            """
        )
    )

    for table_name, prefix, sequence_name in RECORD_NUMBER_CONFIG:
        prefix_length = len(prefix) + 2
        op.execute(
            sa.text(
                f"""
                WITH numbered AS (
                    SELECT id, ROW_NUMBER() OVER (ORDER BY created_at ASC, id ASC) AS number_value
                    FROM {table_name}
                )
                UPDATE {table_name} AS target
                SET record_number = :prefix || '-' || LPAD(numbered.number_value::text, 3, '0')
                FROM numbered
                WHERE target.id = numbered.id
                """
            ).bindparams(prefix=prefix)
        )
        op.execute(
            sa.text(
                f"""
                SELECT setval(
                    '{sequence_name}',
                    COALESCE(MAX(SUBSTRING(record_number FROM {prefix_length})::bigint), 1),
                    COUNT(*) > 0
                )
                FROM {table_name}
                """
            )
        )
        op.alter_column(table_name, "record_number", nullable=False)
        op.create_unique_constraint(
            f"uq_{table_name}_record_number",
            table_name,
            ["record_number"],
        )
        op.execute(
            sa.text(
                f"""
                CREATE FUNCTION assign_{table_name}_record_number()
                RETURNS trigger AS $$
                BEGIN
                    IF NEW.record_number IS NOT NULL THEN
                        RAISE EXCEPTION 'record_number is assigned by PostgreSQL';
                    END IF;
                    NEW.record_number := '{prefix}-' || LPAD(nextval('{sequence_name}')::text, 3, '0');
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                CREATE TRIGGER trg_assign_{table_name}_record_number
                BEFORE INSERT ON {table_name}
                FOR EACH ROW EXECUTE FUNCTION assign_{table_name}_record_number();

                CREATE TRIGGER trg_prevent_{table_name}_record_number_change
                BEFORE UPDATE ON {table_name}
                FOR EACH ROW
                WHEN (OLD.record_number IS DISTINCT FROM NEW.record_number)
                EXECUTE FUNCTION prevent_record_number_change();
                """
            )
        )


def downgrade() -> None:
    """Remove Phase 1 objects only before production writes occur."""
    for table_name, _, sequence_name in reversed(RECORD_NUMBER_CONFIG):
        op.execute(
            sa.text(
                f"DROP TRIGGER trg_prevent_{table_name}_record_number_change ON {table_name}"
            )
        )
        op.execute(sa.text(f"DROP TRIGGER trg_assign_{table_name}_record_number ON {table_name}"))
        op.execute(sa.text(f"DROP FUNCTION assign_{table_name}_record_number()"))
        op.drop_constraint(f"uq_{table_name}_record_number", table_name, type_="unique")
        op.drop_column(table_name, "record_number")
        op.execute(sa.text(f"DROP SEQUENCE {sequence_name}"))

    for table_name in ("user_stories", "requirements", "projects"):
        op.drop_constraint(
            f"fk_{table_name}_created_by_id_users",
            table_name,
            type_="foreignkey",
        )
        op.drop_index(f"ix_{table_name}_created_by_id", table_name=table_name)
        op.drop_column(table_name, "created_by_id")

    op.execute(sa.text("DROP FUNCTION prevent_record_number_change()"))
