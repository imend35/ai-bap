
"""I store the audit history of user story approval decisions."""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UserStoryApprovalAudit(Base):
    """I record who approved or rejected a user story and when."""

    __tablename__ = "user_story_approval_audits"

    # I assign a unique identifier to each audit record.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # I link the decision to its user story when it still exists.
    user_story_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_stories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # I identify the user who performed the decision.
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # I preserve the original user story identifier.
    user_story_id_snapshot: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # I preserve the original actor identifier.
    actor_id_snapshot: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )

    # I record the type of approval decision.
    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # I preserve the status before and after the decision.
    previous_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    new_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # I let PostgreSQL record the decision timestamp.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # I enforce the supported approval and rejection decisions.
    __table_args__ = (
        CheckConstraint(
            "action IN ('approved', 'rejected')",
            name="ck_user_story_audit_action",
        ),
        CheckConstraint(
            "previous_status = 'in_review'",
            name="ck_user_story_audit_previous_status",
        ),
        CheckConstraint(
            "new_status = action",
            name="ck_user_story_audit_new_status",
        ),
    )
