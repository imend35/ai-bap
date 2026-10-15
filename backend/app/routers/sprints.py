
"""Provide API endpoints for sprint management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, Sprint
from app.schemas.sprint import (
    SprintCreate,
    SprintListResponse,
    SprintResponse,
    SprintUpdate,
)
from app.security import verify_demo_token


router = APIRouter(
    prefix="/api/v1/sprints",
    tags=["Sprints"],
    dependencies=[Depends(verify_demo_token)],
)


@router.get("", response_model=SprintListResponse)
def list_sprints(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SprintListResponse:
    """Return a paginated list of sprints for a project."""
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    total = db.scalar(
        select(func.count())
        .select_from(Sprint)
        .where(Sprint.project_id == project_id)
    ) or 0

    statement = (
        select(Sprint)
        .where(Sprint.project_id == project_id)
        .order_by(Sprint.created_at.desc(), Sprint.id.desc())
        .limit(limit)
        .offset(offset)
    )

    sprints = db.scalars(statement).all()

    return SprintListResponse(
        items=sprints,
        total=total,
        limit=limit,
        offset=offset,
    )

@router.post(
    "",
    response_model=SprintResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_sprint(
    payload: SprintCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Sprint:
    """Create a sprint for an existing project."""
    project = db.get(Project, payload.project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    sprint = Sprint(
        project_id=payload.project_id,
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=payload.status.value,
    )

    db.add(sprint)
    db.commit()
    db.refresh(sprint)

    return sprint

@router.get(
    "/{sprint_id}",
    response_model=SprintResponse,
)
def get_sprint(
    sprint_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Sprint:
    """Return a single sprint by its unique identifier."""
    sprint = db.get(Sprint, sprint_id)

    if sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found.",
        )

    return sprint

@router.patch(
    "/{sprint_id}",
    response_model=SprintResponse,
)
def update_sprint(
    sprint_id: UUID,
    payload: SprintUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Sprint:
    """Update a sprint while preserving a valid date range."""
    sprint = db.get(Sprint, sprint_id)

    if sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found.",
        )

    changes = payload.model_dump(exclude_unset=True)

    start_date = changes.get("start_date", sprint.start_date)
    end_date = changes.get("end_date", sprint.end_date)

    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sprint end_date must be on or after start_date.",
        )

    for field_name, value in changes.items():
        if field_name == "status":
            value = value.value

        setattr(sprint, field_name, value)

    db.commit()
    db.refresh(sprint)

    return sprint
