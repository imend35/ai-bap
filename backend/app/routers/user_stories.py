
"""Provide API endpoints for user story management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Requirement, UserStory
from app.schemas.ai_user_story import (
    AIUserStoryGenerateRequest,
    AIUserStoryGenerateResponse,
)
from app.schemas.user_story import (
    UserStoryCreate,
    UserStoryListResponse,
    UserStoryResponse,
    UserStoryUpdate,
)
from app.security import verify_demo_token
from app.services.ai.user_story_generator import (
    AIGenerationError,
    generate_user_story,
)

router = APIRouter(
    prefix="/api/v1/user-stories",
    tags=["User Stories"],
    dependencies=[Depends(verify_demo_token)],
)


@router.get("", response_model=UserStoryListResponse)
def list_user_stories(
    requirement_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> UserStoryListResponse:
    """Return a paginated list of user stories for a requirement."""

    requirement = db.get(Requirement, requirement_id)

    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found.",
        )

    total = db.scalar(
        select(func.count())
        .select_from(UserStory)
        .where(UserStory.requirement_id == requirement_id)
    ) or 0

    statement = (
        select(UserStory)
        .where(UserStory.requirement_id == requirement_id)
        .order_by(UserStory.created_at.desc(), UserStory.id.desc())
        .limit(limit)
        .offset(offset)
    )

    stories = db.scalars(statement).all()

    return UserStoryListResponse(
        items=stories,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "",
    response_model=UserStoryResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_story(
    payload: UserStoryCreate,
    db: Annotated[Session, Depends(get_db)],
) -> UserStory:
    """Create a new user story for an existing requirement."""

    requirement = db.get(Requirement, payload.requirement_id)

    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found.",
        )

    story = UserStory(
        requirement_id=payload.requirement_id,
        title=payload.title,
        description=payload.description,
        acceptance_criteria=payload.acceptance_criteria,
        status=payload.status.value,
    )

    db.add(story)
    db.commit()
    db.refresh(story)

    return story


@router.post(
    "/generate",
    response_model=AIUserStoryGenerateResponse,
    status_code=status.HTTP_200_OK,
)
def generate_user_story_draft(
    payload: AIUserStoryGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AIUserStoryGenerateResponse:
    """Generate an AI-assisted user story draft without saving it."""

    # Öncelikle ilgili gereksinimin veritabanında bulunduğunu kontrol ediyorum.
    requirement = db.get(Requirement, payload.requirement_id)

    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found.",
        )

    try:
        # Gereksinim bilgilerini AI servisine göndererek taslak oluşturuyorum.
        generated_story = generate_user_story(
            requirement_title=requirement.title,
            requirement_description=requirement.description,
            requirement_priority=requirement.priority,
        )

    except AIGenerationError as exc:
        # AI servis hatalarını kontrollü bir API yanıtına dönüştürüyorum.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI user story generation is currently unavailable.",
        ) from exc

    # AI taslağını kaydetmeden kullanıcı incelemesine sunuyorum.
    return AIUserStoryGenerateResponse(
        requirement_id=requirement.id,
        title=generated_story.title,
        description=generated_story.description,
        acceptance_criteria=generated_story.acceptance_criteria,
        requires_human_review=True,
        saved_to_database=False,
    )


@router.get(
    "/{story_id}",
    response_model=UserStoryResponse,
)
def get_user_story(
    story_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> UserStory:
    """Return a single user story by its unique identifier."""

    story = db.get(UserStory, story_id)

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Story not found.",
        )

    return story


@router.patch(
    "/{story_id}",
    response_model=UserStoryResponse,
)
def update_user_story(
    story_id: UUID,
    payload: UserStoryUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> UserStory:
    """Update only the provided fields of an existing user story."""

    story = db.get(UserStory, story_id)

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Story not found.",
        )

    update_data = payload.model_dump(
        exclude_unset=True,
        mode="json",
    )

    for field_name, value in update_data.items():
        setattr(story, field_name, value)

    db.commit()
    db.refresh(story)

    return story
