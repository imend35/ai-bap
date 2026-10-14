
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.requirement import Requirement


class UserStory(Base):
    """Represent a user story linked to a requirement."""

    __tablename__ = "user_stories"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
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
