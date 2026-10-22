
"""I provide JWT-protected API endpoints for requirement management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Project, Requirement
from app.models.user import User
from app.role_permissions import (
    ADMIN,
    BUSINESS_ANALYST,
    REVIEWER,
    require_roles,
)
from app.schemas.requirement import (
    RequirementCreate,
    RequirementListResponse,
    RequirementResponse,
    RequirementUpdate,
)
from app.services.project_archive import (
    lock_writable_project,
    resolve_project_id_for_requirement,
)

router = APIRouter(
    prefix="/api/v1/requirements",
    tags=["Requirements"],
)


@router.get(
    "",
    response_model=RequirementListResponse,
    dependencies=[Depends(require_roles(ADMIN, BUSINESS_ANALYST, REVIEWER))],
)
def list_requirements(
    project_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> RequirementListResponse:
    """I return a paginated list of requirements for an authorized user."""

    # I verify that the requested project exists.
    project = db.get(Project, project_id)

    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found.",
        )

    # I count the requirements belonging to the selected project.
    total = db.scalar(
        select(func.count())
        .select_from(Requirement)
        .where(Requirement.project_id == project_id)
    ) or 0

    # I retrieve requirements using consistent pagination and ordering.
    statement = (
        select(Requirement)
        .options(selectinload(Requirement.created_by))
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
    current_user: Annotated[
        User,
        Depends(require_roles(ADMIN, BUSINESS_ANALYST)),
    ],
) -> Requirement:
    """I create a requirement when the user has editing permissions."""

    # I lock and verify the parent project before creating a requirement.
    lock_writable_project(db, payload.project_id)

    # I preserve the existing requirement creation behavior.
    requirement = Requirement(
        created_by_id=current_user.id,
        project_id=payload.project_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority.value,
        status=payload.status.value,
    )

    db.add(requirement)
    db.commit()
    db.refresh(requirement)

    # I retain the authenticated creator for response serialization.
    requirement.created_by = current_user

    return requirement


@router.get(
    "/{requirement_id}",
    response_model=RequirementResponse,
    dependencies=[Depends(require_roles(ADMIN, BUSINESS_ANALYST, REVIEWER))],
)
def get_requirement(
    requirement_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Requirement:
    """I return an existing requirement to an authorized user."""

    # I retrieve the requested requirement by its unique identifier.
    requirement = db.scalar(
        select(Requirement)
        .options(selectinload(Requirement.created_by))
        .where(Requirement.id == requirement_id)
    )

    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found.",
        )

    return requirement


@router.patch(
    "/{requirement_id}",
    response_model=RequirementResponse,
    dependencies=[Depends(require_roles(ADMIN, BUSINESS_ANALYST))],
)
def update_requirement(
    requirement_id: UUID,
    payload: RequirementUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Requirement:
    """I update a requirement when the user has editing permissions."""

    project_id = resolve_project_id_for_requirement(db, requirement_id)

    if project_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found.",
        )

    # I lock and verify the parent project before retrieving the requirement.
    lock_writable_project(db, project_id)

    # I verify that the requirement still exists before applying changes.
    requirement = db.get(Requirement, requirement_id)

    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found.",
        )

    # I update only the fields explicitly provided in the request.
    update_data = payload.model_dump(
        exclude_unset=True,
        mode="json",
    )

    for field_name, value in update_data.items():
        setattr(requirement, field_name, value)

    # I save the changes and refresh the requirement.
    db.commit()
    db.refresh(requirement)

    return db.scalar(
        select(Requirement)
        .options(selectinload(Requirement.created_by))
        .where(Requirement.id == requirement_id)
    ) or requirement
