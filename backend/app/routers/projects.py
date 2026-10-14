
"""Provide API endpoints for project management."""


from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project
from app.schemas import ProjectCreate, ProjectListResponse, ProjectResponse, ProjectUpdate
from app.security import verify_demo_token

router = APIRouter(
    prefix="/api/v1/projects",
    tags=["Projects"],
    dependencies=[Depends(verify_demo_token)],
)


@router.get("", response_model=ProjectListResponse)
def list_projects(
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ProjectListResponse:
    """Return a paginated list of projects."""
    total = db.scalar(select(func.count()).select_from(Project)) or 0

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
) -> Project:
    """Create a project and persist it in PostgreSQL."""
    project = Project(
        name=payload.name,
        description=payload.description,
        status=payload.status.value,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Project:
    """Return a project by its unique identifier."""
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
) -> Project:
    """Update the supplied fields of an existing project."""
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    update_data = payload.model_dump(exclude_unset=True)

    for field_name, value in update_data.items():
        if field_name == "status" and value is not None:
            value = value.value

        setattr(project, field_name, value)

    db.add(project)
    db.commit()
    db.refresh(project)

    return project
