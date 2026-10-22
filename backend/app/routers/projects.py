
"""I provide JWT-protected API endpoints for project management."""

from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Project, Requirement, Sprint, Task, UserStory
from app.models.user import User
from app.role_permissions import (
    ADMIN,
    BUSINESS_ANALYST,
    REVIEWER,
    require_roles,
)
from app.schemas import (
    ProjectCreate,
    ProjectListResponse,
    ProjectResponse,
    ProjectUpdate,
)
from app.schemas.project import (
    ProjectDashboardResponse,
    ProjectTraceabilityResponse,
    TraceabilityRequirement,
    TraceabilityStory,
    TraceabilityTask,
)

router = APIRouter(
    prefix="/api/v1/projects",
    tags=["Projects"],
)


def get_project_with_relationships(
    db: Session,
    project_id: UUID,
    *,
    for_update: bool = False,
) -> Project | None:
    """I retrieve a project with the actor identities used in responses."""
    statement = (
        select(Project)
        .options(
            selectinload(Project.created_by),
            selectinload(Project.archived_by),
        )
        .where(Project.id == project_id)
    )

    if for_update:
        statement = statement.with_for_update()

    return db.scalar(statement)


@router.get("", response_model=ProjectListResponse)
def list_projects(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(ADMIN, BUSINESS_ANALYST, REVIEWER)),
    ],
    archived: bool = False,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProjectListResponse:
    """I return a paginated list of projects for authorized users."""

    archive_filter = (
        Project.archived_at.is_not(None)
        if archived
        else Project.archived_at.is_(None)
    )

    # I count the selected archive state before pagination.
    total = db.scalar(
        select(func.count()).select_from(Project).where(archive_filter)
    ) or 0

    # I retrieve the requested project page.
    statement = (
        select(Project)
        .options(
            selectinload(Project.created_by),
            selectinload(Project.archived_by),
        )
        .where(archive_filter)
        .order_by(Project.created_at.desc(), Project.id.desc())
        .limit(limit)
        .offset(offset)
    )

    projects = db.scalars(statement).all()

    return ProjectListResponse(
        items=projects,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    payload: ProjectCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(ADMIN, BUSINESS_ANALYST)),
    ],
) -> Project:
    """I create a project as an authorized user."""

    # I prepare the project from the validated request.
    project = Project(
        created_by_id=current_user.id,
        name=payload.name,
        description=payload.description,
        status=payload.status.value,
    )

    # I save the project in PostgreSQL.
    db.add(project)
    db.commit()
    db.refresh(project)

    # I retain the authenticated creator for response serialization.
    project.created_by = current_user
    project.archived_by = None

    return project


@router.get(
    "/{project_id}/dashboard",
    response_model=ProjectDashboardResponse,
    operation_id="getProjectDashboard",
)
def get_project_dashboard(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(ADMIN, BUSINESS_ANALYST, REVIEWER)),
    ],
) -> ProjectDashboardResponse:
    """I return persisted-record delivery counts for an authorized project reader."""

    # I retain the established project-not-found behavior before aggregating.
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    # I count requirements directly scoped to the requested project.
    total_requirements = db.scalar(
        select(func.count())
        .select_from(Requirement)
        .where(Requirement.project_id == project_id)
    ) or 0

    # I count only stories carrying the persisted approved workflow status.
    approved_user_stories = db.scalar(
        select(func.count())
        .select_from(UserStory)
        .join(Requirement, UserStory.requirement_id == Requirement.id)
        .where(
            Requirement.project_id == project_id,
            UserStory.status == "approved",
        )
    ) or 0

    # I aggregate every project task status without loading relationship collections.
    task_status_rows = db.execute(
        select(Task.status, func.count())
        .join(UserStory, Task.story_id == UserStory.id)
        .join(Requirement, UserStory.requirement_id == Requirement.id)
        .where(Requirement.project_id == project_id)
        .group_by(Task.status)
    ).all()
    tasks_by_status = {
        "todo": 0,
        "in_progress": 0,
        "in_review": 0,
        "done": 0,
    }
    tasks_by_status.update(
        {task_status: count for task_status, count in task_status_rows}
    )

    # I count persisted active sprint status rather than inferring activity from dates.
    active_sprints = db.scalar(
        select(func.count())
        .select_from(Sprint)
        .where(
            Sprint.project_id == project_id,
            Sprint.status == "active",
        )
    ) or 0

    return ProjectDashboardResponse(
        project_id=project_id,
        total_requirements=total_requirements,
        approved_user_stories=approved_user_stories,
        tasks_by_status=tasks_by_status,
        active_sprints=active_sprints,
    )


@router.get(
    "/{project_id}/traceability",
    response_model=ProjectTraceabilityResponse,
    operation_id="getProjectTraceability",
)
def get_project_traceability(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(ADMIN, BUSINESS_ANALYST, REVIEWER)),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProjectTraceabilityResponse:
    """I return a paginated Requirement-to-Story-to-Task project hierarchy."""

    # I retain the established project-not-found behavior before reading data.
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    # I count every root Requirement in the selected project.
    total = db.scalar(
        select(func.count())
        .select_from(Requirement)
        .where(Requirement.project_id == project_id)
    ) or 0

    # I retrieve only the requested roots using the established stable ordering.
    requirements = db.scalars(
        select(Requirement)
        .where(Requirement.project_id == project_id)
        .order_by(Requirement.created_at.desc(), Requirement.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    requirement_ids = [requirement.id for requirement in requirements]

    # I fetch all stories for the returned roots in one set-based query.
    stories = (
        db.scalars(
            select(UserStory)
            .where(UserStory.requirement_id.in_(requirement_ids))
            .order_by(UserStory.created_at.desc(), UserStory.id.desc())
        ).all()
        if requirement_ids
        else []
    )
    story_ids = [story.id for story in stories]

    # I fetch all tasks for those stories in one set-based query.
    tasks = (
        db.scalars(
            select(Task)
            .where(Task.story_id.in_(story_ids))
            .order_by(Task.created_at.desc(), Task.id.desc())
        ).all()
        if story_ids
        else []
    )

    tasks_by_story: dict[UUID, list[TraceabilityTask]] = {
        story_id: [] for story_id in story_ids
    }
    for task in tasks:
        tasks_by_story[task.story_id].append(
            TraceabilityTask(
                id=task.id,
                title=task.title,
                status=task.status,
            )
        )

    stories_by_requirement: dict[UUID, list[TraceabilityStory]] = {
        requirement_id: [] for requirement_id in requirement_ids
    }
    for story in stories:
        stories_by_requirement[story.requirement_id].append(
            TraceabilityStory(
                id=story.id,
                record_number=story.record_number,
                title=story.title,
                status=story.status,
                tasks=tasks_by_story[story.id],
            )
        )

    return ProjectTraceabilityResponse(
        items=[
            TraceabilityRequirement(
                id=requirement.id,
                record_number=requirement.record_number,
                title=requirement.title,
                status=requirement.status,
                priority=requirement.priority,
                stories=stories_by_requirement[requirement.id],
            )
            for requirement in requirements
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/{project_id}/archive",
    response_model=ProjectResponse,
    operation_id="archiveProject",
)
def archive_project(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(ADMIN)),
    ],
) -> Project:
    """I archive a project without changing its workflow statuses."""

    project = get_project_with_relationships(
        db,
        project_id,
        for_update=True,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    if project.archived_at is None:
        project.archived_at = datetime.now(UTC)
        project.archived_by_id = current_user.id
        project.archived_by = current_user
        db.commit()
        db.expire(project)

        return get_project_with_relationships(db, project_id) or project

    return project


@router.post(
    "/{project_id}/restore",
    response_model=ProjectResponse,
    operation_id="restoreProject",
)
def restore_project(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(ADMIN)),
    ],
) -> Project:
    """I restore a project without changing its workflow statuses."""

    project = get_project_with_relationships(
        db,
        project_id,
        for_update=True,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    if project.archived_at is not None:
        project.archived_at = None
        project.archived_by_id = None
        project.archived_by = None
        db.commit()
        db.expire(project)

        return get_project_with_relationships(db, project_id) or project

    return project


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(ADMIN, BUSINESS_ANALYST, REVIEWER)),
    ],
) -> Project:
    """I return a project by its unique identifier."""

    # I retrieve the requested project.
    project = get_project_with_relationships(db, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(ADMIN, BUSINESS_ANALYST)),
    ],
) -> Project:
    """I update an existing project as an authorized user."""

    # I lock the requested project for the archive-state check and mutation.
    project = get_project_with_relationships(
        db,
        project_id,
        for_update=True,
    )

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    if project.archived_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Archived projects are read-only. Restore the project before "
                "making changes."
            ),
        )

    # I apply only the fields provided in the request.
    update_data = payload.model_dump(exclude_unset=True)

    for field_name, value in update_data.items():
        if field_name == "status" and value is not None:
            value = value.value

        setattr(project, field_name, value)

    # I persist the updated project.
    db.add(project)
    db.commit()
    db.expire(project)

    return get_project_with_relationships(db, project_id) or project
