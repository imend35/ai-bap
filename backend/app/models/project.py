
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.requirement import Requirement
    from app.models.sprint import Sprint

class Project(Base):
    """Represent a business analysis project."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
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

    requirements: Mapped[list["Requirement"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
    sprints: Mapped[list["Sprint"]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )