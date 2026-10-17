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
    AdminUserUpdate,
)

router = APIRouter(prefix="/api/v1/admin/users", tags=["Admin Users"])


def change_user_activation(
    user_id: UUID,
    is_active: bool,
    db: Session,
    current_user: User,
) -> User:
    """Change account activation while preserving active-admin availability."""

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

        user = db.scalar(select(User).where(User.id == user_id).with_for_update())
        if user is None:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        if not is_active and user.is_active and user.role == ADMIN:
            active_admin_count = (
                db.scalar(
                    select(func.count())
                    .select_from(User)
                    .where(User.role == ADMIN, User.is_active.is_(True))
                )
                or 0
            )
            if active_admin_count <= 1:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="The last active administrator cannot be deactivated.",
                )

        if user.is_active != is_active:
            user.is_active = is_active
            db.commit()
            db.refresh(user)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update user activation.",
        ) from None

    return user


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


@router.post(
    "/{user_id}/activate",
    response_model=AdminUserResponse,
    operation_id="activateAdminUser",
)
def activate_user(
    user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(ADMIN))],
) -> User:
    """Activate a platform user as an active administrator."""

    return change_user_activation(user_id, True, db, current_user)


@router.post(
    "/{user_id}/deactivate",
    response_model=AdminUserResponse,
    operation_id="deactivateAdminUser",
)
def deactivate_user(
    user_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(ADMIN))],
) -> User:
    """Deactivate a platform user while retaining an active administrator."""

    return change_user_activation(user_id, False, db, current_user)


@router.patch("/{user_id}", response_model=AdminUserResponse)
def update_user(
    user_id: UUID,
    payload: AdminUserUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[User, Depends(require_roles(ADMIN))],
) -> User:
    """Update a user's name or role while preserving the active-admin invariant."""

    try:
        if "role" in payload.model_fields_set:
            # This also covers a no-op role PATCH. Serializing all requested role
            # changes keeps active-admin membership checks safe and straightforward.
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

            user = db.scalar(select(User).where(User.id == user_id).with_for_update())
        else:
            user = db.get(User, user_id)

        if user is None:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found.",
            )

        requested_role = payload.role
        if (
            "role" in payload.model_fields_set
            and user.role == ADMIN
            and requested_role != ADMIN
            and user.is_active
        ):
            active_admin_count = db.scalar(
                select(func.count())
                .select_from(User)
                .where(User.role == ADMIN, User.is_active.is_(True))
            ) or 0
            if active_admin_count <= 1:
                db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="The last active administrator cannot be demoted.",
                )

        if "full_name" in payload.model_fields_set:
            user.full_name = payload.full_name
        if "role" in payload.model_fields_set:
            user.role = requested_role

        db.commit()
        db.refresh(user)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to update user.",
        ) from None

    return user
