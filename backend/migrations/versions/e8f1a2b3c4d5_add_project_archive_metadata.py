"""add project archive metadata

Revision ID: e8f1a2b3c4d5
Revises: d4e5f6a7b8c9
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "e8f1a2b3c4d5"
down_revision: str | Sequence[str] | None = "d4e5f6a7b8c9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add nullable project archive metadata and integrity guarantees."""
    op.add_column(
        "projects",
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "projects",
        sa.Column("archived_by_id", sa.UUID(), nullable=True),
    )
    op.create_foreign_key(
        "fk_projects_archived_by_id_users",
        "projects",
        "users",
        ["archived_by_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_projects_archive_metadata_paired",
        "projects",
        "(archived_at IS NULL AND archived_by_id IS NULL) OR "
        "(archived_at IS NOT NULL AND archived_by_id IS NOT NULL)",
    )
    op.create_index(
        "ix_projects_archived_at",
        "projects",
        ["archived_at"],
        unique=False,
    )
    op.create_index(
        "ix_projects_archived_by_id",
        "projects",
        ["archived_by_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove project archive metadata and its database objects."""
    op.drop_index("ix_projects_archived_by_id", table_name="projects")
    op.drop_index("ix_projects_archived_at", table_name="projects")
    op.drop_constraint(
        "ck_projects_archive_metadata_paired",
        "projects",
        type_="check",
    )
    op.drop_constraint(
        "fk_projects_archived_by_id_users",
        "projects",
        type_="foreignkey",
    )
    op.drop_column("projects", "archived_by_id")
    op.drop_column("projects", "archived_at")
