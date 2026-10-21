
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    FetchedValue,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.requirement import Requirement
    from app.models.sprint import Sprint
    from app.models.user import User


class Project(Base):
    """Represent a business analysis project."""

    __tablename__ = "projects"

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

    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        Enum(
            "planned",
            "active",
            "on_hold",
            "completed",
            name="project_status",
        ),
        nullable=False,
        default="planned",
        server_default="planned",
    )

    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    archived_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
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

    __table_args__ = (
        CheckConstraint(
            "(archived_at IS NULL AND archived_by_id IS NULL) OR "
            "(archived_at IS NOT NULL AND archived_by_id IS NOT NULL)",
            name="ck_projects_archive_metadata_paired",
        ),
    )

    requirements: Mapped[list["Requirement"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    sprints: Mapped[list["Sprint"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    created_by: Mapped["User | None"] = relationship(
        back_populates="created_projects",
        foreign_keys=[created_by_id],
    )
    archived_by: Mapped["User | None"] = relationship(
        back_populates="archived_projects",
        foreign_keys=[archived_by_id],
    )
