
"""I manage user registration and authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.jwt_service import create_access_token
from app.models.user import User
from app.password_service import hash_password, verify_password
from app.schemas.auth import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)


router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    payload: UserRegister,
    db: Annotated[Session, Depends(get_db)],
) -> User:
    """I register a new user with a securely hashed password."""

    # I normalize email addresses before checking for duplicates.
    normalized_email = str(payload.email).strip().lower()

    existing_user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    # I assign the least-privileged registration role.
    new_user = User(
        email=normalized_email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        role="business_analyst",
        is_active=True,
    )

    db.add(new_user)

    try:
        # I commit the new user and reload database-generated values.
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        # I handle concurrent registrations using the same email.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        ) from None

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
)
def login_user(
    payload: UserLogin,
    db: Annotated[Session, Depends(get_db)],
) -> TokenResponse:
    """I authenticate a user and issue a signed JWT access token."""

    # I normalize the email address before searching for the user.
    normalized_email = str(payload.email).strip().lower()

    user = db.scalar(
        select(User).where(User.email == normalized_email)
    )

    # I use the same error message for invalid login credentials.
    if user is None or not verify_password(
        payload.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # I prevent inactive accounts from receiving access tokens.
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive.",
        )

    # I issue an access token containing the authenticated user ID.
    access_token = create_access_token(user.id)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )
