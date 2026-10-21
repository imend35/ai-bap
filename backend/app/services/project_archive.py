"""Provide project archive-state resolution and write guards.

Callers must authorize before invoking these helpers. For descendant writes,
callers resolve the parent project ID without locking a descendant, lock and
check the project, then retrieve or lock the descendant in the same session
transaction. The helpers do not commit, roll back, close, or create sessions.

AI generation should use a short initial transaction to lock and check the
project before provider invocation, release that lock before the external call,
and lock/check again in a new transaction before persisting generated content.
"""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Project, Requirement, Sprint, Task, UserStory


ARCHIVED_PROJECT_READ_ONLY_DETAIL = (
    "Archived projects are read-only. Restore the project before making changes."
)


def lock_project(db: Session, project_id: UUID) -> Project:
    """Lock and return a project, or retain the established project 404."""
    project = db.scalar(
        select(Project)
        .where(Project.id == project_id)
        .execution_options(populate_existing=True)
        .with_for_update(of=Project)
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    return project


def ensure_project_writable(project: Project) -> Project:
    """Reject writes when the caller's locked project is archived."""
    if project.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ARCHIVED_PROJECT_READ_ONLY_DETAIL,
        )

    return project


def lock_writable_project(db: Session, project_id: UUID) -> Project:
    """Lock a project and verify that normal mutations are allowed."""
    return ensure_project_writable(lock_project(db, project_id))


def resolve_project_id_for_requirement(
    db: Session,
    requirement_id: UUID,
) -> UUID | None:
    """Resolve a requirement's parent project without locking either row."""
    return db.scalar(
        select(Requirement.project_id).where(Requirement.id == requirement_id)
    )


def resolve_project_id_for_user_story(
    db: Session,
    story_id: UUID,
) -> UUID | None:
    """Resolve a user story's parent project without locking descendant rows."""
    return db.scalar(
        select(Requirement.project_id)
        .join(UserStory, UserStory.requirement_id == Requirement.id)
        .where(UserStory.id == story_id)
    )


def resolve_project_id_for_task(
    db: Session,
    task_id: UUID,
) -> UUID | None:
    """Resolve a task's parent project without locking descendant rows."""
    return db.scalar(
        select(Requirement.project_id)
        .join(UserStory, UserStory.requirement_id == Requirement.id)
        .join(Task, Task.story_id == UserStory.id)
        .where(Task.id == task_id)
    )


def resolve_project_id_for_sprint(
    db: Session,
    sprint_id: UUID,
) -> UUID | None:
    """Resolve a sprint's parent project without locking descendant rows."""
    return db.scalar(
        select(Sprint.project_id).where(Sprint.id == sprint_id)
    )
