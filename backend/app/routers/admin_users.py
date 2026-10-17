"""Provide administrator-only read endpoints for platform users."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.role_permissions import ADMIN, require_roles
from app.schemas.admin_user import AdminUserListResponse, AdminUserResponse

router = APIRouter(prefix="/api/v1/admin/users", tags=["Admin Users"])


@router.get("", response_model=AdminUserListResponse)
def list_users(
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(ADMIN))],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AdminUserListResponse:
    """Return all platform users, including inactive accounts, to an admin."""

    total = db.scalar(select(func.count()).select_from(User)) or 0
    users = db.scalars(
        select(User)
        .order_by(User.created_at.desc(), User.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()

    return AdminUserListResponse(
        items=users,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{user_id}", response_model=AdminUserResponse)
def get_user(
    user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(ADMIN))],
) -> User:
    """Return one platform user, including an inactive account, to an admin."""

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user
