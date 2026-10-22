
"""I provide secure API endpoints for sprint management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, Sprint
from app.role_permissions import (
    ADMIN,
    BUSINESS_ANALYST,
    REVIEWER,
    require_roles,
)
from app.schemas.sprint import (
    SprintCreate,
    SprintListResponse,
    SprintResponse,
    SprintUpdate,
)
from app.services.project_archive import (
    lock_writable_project,
    resolve_project_id_for_sprint,
)

router = APIRouter(
    prefix="/api/v1/sprints",
    tags=["Sprints"],
)


@router.get(
    "",
    response_model=SprintListResponse,
    dependencies=[
        Depends(require_roles(ADMIN, BUSINESS_ANALYST, REVIEWER))
    ],
)
def list_sprints(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SprintListResponse:
    """I return a paginated list of sprints for a project."""

    # I verify that the requested project exists.
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    # I count all sprints belonging to the requested project.
    total = db.scalar(
        select(func.count())
        .select_from(Sprint)
        .where(Sprint.project_id == project_id)
    ) or 0

    # I retrieve sprints using stable ordering and pagination.
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
    dependencies=[
        Depends(require_roles(ADMIN, BUSINESS_ANALYST))
    ],
)
def create_sprint(
    payload: SprintCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Sprint:
    """I create a sprint for an existing project."""

    # I lock the parent project and verify that it accepts writes.
    lock_writable_project(db, payload.project_id)

    # I create the sprint using the validated request payload.
    sprint = Sprint(
        project_id=payload.project_id,
        name=payload.name,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=payload.status.value,
    )

    # I persist the sprint and refresh its database-generated fields.
    db.add(sprint)
    db.commit()
    db.refresh(sprint)

    return sprint


@router.get(
    "/{sprint_id}",
    response_model=SprintResponse,
    dependencies=[
        Depends(require_roles(ADMIN, BUSINESS_ANALYST, REVIEWER))
    ],
)
def get_sprint(
    sprint_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Sprint:
    """I return a single sprint by its unique identifier."""

    # I retrieve the requested sprint from the database.
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
    dependencies=[
        Depends(require_roles(ADMIN, BUSINESS_ANALYST))
    ],
)
def update_sprint(
    sprint_id: UUID,
    payload: SprintUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Sprint:
    """I update a sprint while preserving a valid date range."""

    project_id = resolve_project_id_for_sprint(db, sprint_id)
    if project_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found.",
        )

    lock_writable_project(db, project_id)

    # I verify that the sprint exists before applying changes.
    sprint = db.get(Sprint, sprint_id)

    if sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found.",
        )

    # I extract only the fields explicitly provided in the request.
    changes = payload.model_dump(exclude_unset=True)

    start_date = changes.get("start_date", sprint.start_date)
    end_date = changes.get("end_date", sprint.end_date)

    # I prevent updates that would create an invalid date range.
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sprint end_date must be on or after start_date.",
        )

    # I apply validated changes and convert enum values for storage.
    for field_name, value in changes.items():
        if field_name == "status":
            value = value.value

        setattr(sprint, field_name, value)

    # I persist the changes and reload the updated sprint.
    db.commit()
    db.refresh(sprint)

    return sprint
