
"""I add the users table with role-based access support.

Revision ID: f3174e415283
Revises: f96458181c12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "f3174e415283"
down_revision: str | Sequence[str] | None = "f96458181c12"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


user_role_enum = postgresql.ENUM(
    "admin",
    "business_analyst",
    "reviewer",
    name="user_role",
    create_type=False,
)


def upgrade() -> None:
    """I create the users table and its required PostgreSQL enum."""

    # I create the user role type before creating the users table.
    user_role_enum.create(op.get_bind(), checkfirst=True)

    # I create the users table without modifying existing tables.
    op.create_table(
        "users",
        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "full_name",
            sa.String(length=160),
            nullable=False,
        ),
        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "role",
            user_role_enum,
            server_default="business_analyst",
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
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

    # I enforce unique email addresses for all platform users.
    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )


def downgrade() -> None:
    """I remove the users table and its PostgreSQL enum."""

    # I remove the email index before dropping the users table.
    op.drop_index(
        "ix_users_email",
        table_name="users",
    )

    # I remove the users table before dropping its enum type.
    op.drop_table("users")

    # I remove the user role type after its dependent table is gone.
    user_role_enum.drop(op.get_bind(), checkfirst=True)
