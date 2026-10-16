
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, FetchedValue, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.requirement import Requirement
    from app.models.task import Task
    from app.models.user import User


class UserStory(Base):
    """Represent a user story linked to a requirement."""

    __tablename__ = "user_stories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    record_number: Mapped[str] = mapped_column(
        String(32),
        unique=True,
        nullable=False,
        server_default=FetchedValue(),
    )

    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    requirement_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("requirements.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    acceptance_criteria: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "in_review",
            "approved",
            "rejected",
            name="user_story_status",
        ),
        nullable=False,
        default="draft",
        server_default="draft",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    requirement: Mapped["Requirement"] = relationship(
        back_populates="user_stories",
    )
    tasks: Mapped[list["Task"]] = relationship(
        back_populates="user_story",
        passive_deletes=True,
    )
    created_by: Mapped["User | None"] = relationship(
        back_populates="created_user_stories",
    )
