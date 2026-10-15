
"""I provide API endpoints for user story management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Requirement, UserStory
from app.role_permissions import ADMIN, REVIEWER
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
from app.security import (
    bearer_scheme,
    get_current_user,
    verify_demo_token,
)
from app.services.ai.user_story_generator import (
    AIGenerationError,
    generate_user_story,
)

router = APIRouter(
    prefix="/api/v1/user-stories",
    tags=["User Stories"],
    dependencies=[Depends(verify_demo_token)],
)

# I define the permitted User Story status transitions.
ALLOWED_STATUS_TRANSITIONS = {
    "draft": {"in_review"},
    "in_review": {"approved", "rejected"},
    "rejected": {"draft"},
    "approved": set(),
}


@router.get("", response_model=UserStoryListResponse)
def list_user_stories(
    requirement_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> UserStoryListResponse:
    """I return a paginated list of user stories for a requirement."""

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
    """I create a new user story for an existing requirement."""

    # I prevent new stories from bypassing human review.
    if payload.status.value != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="New User Stories must start in draft status.",
        )

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
        status="draft",
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
    """I generate an AI-assisted user story draft without saving it."""

    # I verify that the related requirement exists.
    requirement = db.get(Requirement, payload.requirement_id)

    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found.",
        )

    try:
        # I generate a draft using the requirement details.
        generated_story = generate_user_story(
            requirement_title=requirement.title,
            requirement_description=requirement.description,
            requirement_priority=requirement.priority,
        )

    except AIGenerationError as exc:
        # I convert AI service failures into a controlled API response.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI user story generation is currently unavailable.",
        ) from exc

    # I require human review before saving generated content.
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
    """I return a single user story by its unique identifier."""

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
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> UserStory:
    """I update a user story while enforcing approval permissions."""

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

    current_status = story.status
    requested_status = update_data.get("status")

    # I prevent modifications to approved user stories.
    if current_status == "approved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Approved User Stories cannot be modified.",
        )

    # I validate status transitions before applying changes.
    if (
        requested_status is not None
        and requested_status != current_status
    ):
        allowed_statuses = ALLOWED_STATUS_TRANSITIONS.get(
            current_status,
            set(),
        )

        if requested_status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"Invalid User Story status transition: "
                    f"{current_status} -> {requested_status}."
                ),
            )

    # I reserve approval and rejection decisions for authorized users.
    if requested_status in {"approved", "rejected"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Approval and rejection require role-based "
                "JWT authentication, which is not yet enabled "
                "for this demo-token endpoint."
            ),
        )

    # I update only fields permitted by the workflow.
    for field_name, value in update_data.items():
        setattr(story, field_name, value)

    db.commit()
    db.refresh(story)

    return story
