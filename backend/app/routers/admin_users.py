"""Provide administrator-only platform-user management endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.admin_user_lifecycle import acquire_active_admin_lifecycle_lock
from app.database import get_db
from app.models.user import User
from app.password_service import hash_password
from app.role_permissions import ADMIN, require_roles
from app.schemas.admin_user import (
    AdminUserCreate,
    AdminUserListResponse,
    AdminUserResponse,
)

router = APIRouter(prefix="/api/v1/admin/users", tags=["Admin Users"])


@router.post(
    "",
    response_model=AdminUserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    payload: AdminUserCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(ADMIN))],
) -> User:
    """Create a platform user after serializing active-admin lifecycle changes."""

    normalized_email = str(payload.email)

    try:
        acquire_active_admin_lifecycle_lock(db)

        actor = db.scalar(
            select(User)
            .where(
                User.id == current_user.id,
                User.role == ADMIN,
                User.is_active.is_(True),
            )
            .with_for_update()
        )
        if actor is None:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        existing_user = db.scalar(
            select(User.id)
            .where(func.lower(User.email) == normalized_email)
            .limit(1)
        )
        if existing_user is not None:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        new_user = User(
            email=normalized_email,
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
            role=payload.role,
            is_active=payload.is_active,
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create user.",
        ) from None

    return new_user


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
