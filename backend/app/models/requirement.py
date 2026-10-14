
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user_story import UserStory


class Requirement(Base):
    """Represent a requirement belonging to a project."""

    __tablename__ = "requirements"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
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

    priority: Mapped[str] = mapped_column(
        Enum(
            "low",
            "medium",
            "high",
            "critical",
            name="requirement_priority",
        ),
        nullable=False,
        default="medium",
        server_default="medium",
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "draft",
            "in_review",
            "approved",
            "rejected",
            name="requirement_status",
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

    project: Mapped["Project"] = relationship(
        back_populates="requirements",
    )
    user_stories: Mapped[list["UserStory"]] = relationship(
        back_populates="requirement",
        cascade="all, delete-orphan",
    )
