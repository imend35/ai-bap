
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, FetchedValue, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.requirement import Requirement
    from app.models.user_story import UserStory


class User(Base):
    """I represent an authenticated AI BAP platform user."""

    __tablename__ = "users"

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

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        Enum(
            "admin",
            "business_analyst",
            "reviewer",
            name="user_role",
        ),
        nullable=False,
        default="business_analyst",
        server_default="business_analyst",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
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

    created_projects: Mapped[list["Project"]] = relationship(
        back_populates="created_by",
        passive_deletes=True,
        foreign_keys="Project.created_by_id",
    )
    archived_projects: Mapped[list["Project"]] = relationship(
        back_populates="archived_by",
        passive_deletes=True,
        foreign_keys="Project.archived_by_id",
    )
    created_requirements: Mapped[list["Requirement"]] = relationship(
        back_populates="created_by",
        passive_deletes=True,
    )
    created_user_stories: Mapped[list["UserStory"]] = relationship(
        back_populates="created_by",
        passive_deletes=True,
    )
