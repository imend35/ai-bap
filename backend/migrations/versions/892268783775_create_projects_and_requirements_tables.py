
"""Create projects and requirements tables.

Revision ID: 892268783775
Revises:
Create Date: 2026-10-14
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Alembic revision identifiers.
revision: str = "892268783775"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


project_status_enum = postgresql.ENUM(
    "planned",
    "active",
    "on_hold",
    "completed",
    name="project_status",
    create_type=False,
)

requirement_priority_enum = postgresql.ENUM(
    "low",
    "medium",
    "high",
    "critical",
    name="requirement_priority",
    create_type=False,
)

requirement_status_enum = postgresql.ENUM(
    "draft",
    "in_review",
    "approved",
    "rejected",
    name="requirement_status",
    create_type=False,
)


def upgrade() -> None:
    """Create the initial database schema."""

    # Create PostgreSQL enum types before creating the tables.
    project_status_enum.create(op.get_bind(), checkfirst=True)
    requirement_priority_enum.create(op.get_bind(), checkfirst=True)
    requirement_status_enum.create(op.get_bind(), checkfirst=True)

    # Create the projects table.
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "status",
            project_status_enum,
            server_default="planned",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create the requirements table.
    op.create_table(
        "requirements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "priority",
            requirement_priority_enum,
            server_default="medium",
            nullable=False,
        ),
        sa.Column(
            "status",
            requirement_status_enum,
            server_default="draft",
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create an index for project-based requirement queries.
    op.create_index(
        "ix_requirements_project_id",
        "requirements",
        ["project_id"],
        unique=False,
    )


def downgrade() -> None:
    """Remove the initial database schema."""

    # Remove the child table before the parent table.
    op.drop_index(
        "ix_requirements_project_id",
        table_name="requirements",
    )
    op.drop_table("requirements")
    op.drop_table("projects")

    # Remove PostgreSQL enum types after dropping the tables.
    requirement_status_enum.drop(op.get_bind(), checkfirst=True)
    requirement_priority_enum.drop(op.get_bind(), checkfirst=True)
    project_status_enum.drop(op.get_bind(), checkfirst=True)
