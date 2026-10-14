
"""Provide API endpoints for requirement management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, Requirement
from app.schemas.requirement import (
    RequirementCreate,
    RequirementListResponse,
    RequirementResponse,
    RequirementUpdate,
)
from app.security import verify_demo_token

router = APIRouter(
    prefix="/api/v1/requirements",
    tags=["Requirements"],
    dependencies=[Depends(verify_demo_token)],
)


@router.get("", response_model=RequirementListResponse)
def list_requirements(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> RequirementListResponse:
    """Return a paginated list of requirements for a project."""
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    total = db.scalar(
        select(func.count())
        .select_from(Requirement)
        .where(Requirement.project_id == project_id)
    ) or 0

    statement = (
        select(Requirement)
        .where(Requirement.project_id == project_id)
        .order_by(Requirement.created_at.desc(), Requirement.id.desc())
        .limit(limit)
        .offset(offset)
    )

    requirements = db.scalars(statement).all()

    return RequirementListResponse(
        items=requirements,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_requirement(
    payload: RequirementCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Requirement:
    """Create a new requirement for an existing project."""
    project = db.get(Project, payload.project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    requirement = Requirement(
        project_id=payload.project_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority.value,
        status=payload.status.value,
    )

    db.add(requirement)
    db.commit()
    db.refresh(requirement)

    return requirement


@router.get(
    "/{requirement_id}",
    response_model=RequirementResponse,
)
def get_requirement(
    requirement_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Requirement:
    """Return a single requirement by its unique identifier."""
    requirement = db.get(Requirement, requirement_id)

    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found.",
        )

    return requirement


@router.patch(
    "/{requirement_id}",
    response_model=RequirementResponse,
)
def update_requirement(
    requirement_id: UUID,
    payload: RequirementUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Requirement:
    """Update only the provided fields of an existing requirement."""
    requirement = db.get(Requirement, requirement_id)

    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found.",
        )

    update_data = payload.model_dump(exclude_unset=True, mode="json")

    for field_name, value in update_data.items():
        setattr(requirement, field_name, value)

    db.commit()
    db.refresh(requirement)

    return requirement
