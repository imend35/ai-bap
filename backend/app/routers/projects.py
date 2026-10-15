
"""I provide JWT-protected API endpoints for project management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project
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

router = APIRouter(
    prefix="/api/v1/projects",
    tags=["Projects"],
)


@router.get("", response_model=ProjectListResponse)
def list_projects(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(ADMIN, BUSINESS_ANALYST, REVIEWER)),
    ],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProjectListResponse:
    """I return a paginated list of projects for authorized users."""

    # I count the available projects.
    total = db.scalar(select(func.count()).select_from(Project)) or 0

    # I retrieve the requested project page.
    statement = (
        select(Project)
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
        name=payload.name,
        description=payload.description,
        status=payload.status.value,
    )

    # I save the project in PostgreSQL.
    db.add(project)
    db.commit()
    db.refresh(project)

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
    project = db.get(Project, project_id)

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

    # I retrieve the requested project.
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
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
    db.refresh(project)

    return project
