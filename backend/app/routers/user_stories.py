
"""I provide JWT-protected API endpoints for user story management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import Requirement, UserStory
from app.models.user import User
from app.role_permissions import (
    ADMIN,
    BUSINESS_ANALYST,
    REVIEWER,
    require_roles,
)
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
from app.services.ai.user_story_generator import (
    AIGenerationError,
    generate_user_story,
)
from app.services.project_archive import (
    lock_writable_project,
    resolve_project_id_for_requirement,
    resolve_project_id_for_user_story,
)

router = APIRouter(
    prefix="/api/v1/user-stories",
    tags=["User Stories"],
)


# I define valid status transitions for the user story workflow.
ALLOWED_STATUS_TRANSITIONS = {
    "draft": {"in_review"},
    "in_review": {"approved", "rejected"},
    "rejected": {"draft"},
    "approved": set(),
}

# I restrict live generation for the designated public demo identities only.
PUBLIC_DEMO_AI_BLOCKED_EMAILS = frozenset(
    {"banlyst@example.com", "reviwer@example.com"}
)
PUBLIC_DEMO_AI_BLOCKED_DETAIL = (
    "Live AI generation is unavailable for public demo accounts."
)


@router.get(
    "",
    response_model=UserStoryListResponse,
    dependencies=[
        Depends(require_roles(ADMIN, BUSINESS_ANALYST, REVIEWER))
    ],
)
def list_user_stories(
    requirement_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> UserStoryListResponse:
    """I return a paginated list of user stories for a requirement."""

    # I verify that the selected requirement exists.
    requirement = db.get(Requirement, requirement_id)

    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found.",
        )

    # I count the user stories associated with the requirement.
    total = db.scalar(
        select(func.count())
        .select_from(UserStory)
        .where(UserStory.requirement_id == requirement_id)
    ) or 0

    # I retrieve user stories using stable ordering and pagination.
    statement = (
        select(UserStory)
        .options(selectinload(UserStory.created_by))
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
    current_user: Annotated[
        User,
        Depends(require_roles(ADMIN, BUSINESS_ANALYST)),
    ],
) -> UserStory:
    """I create a new user story for an existing requirement."""

    project_id = resolve_project_id_for_requirement(db, payload.requirement_id)

    if project_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found.",
        )

    # I lock and verify the parent project before creating a user story.
    lock_writable_project(db, project_id)

    # I verify that the related requirement still exists.
    requirement = db.get(Requirement, payload.requirement_id)

    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found.",
        )

    # I require all new user stories to start in draft status.
    if payload.status.value != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="New User Stories must start in draft status.",
        )

    # I create the user story without bypassing human review.
    story = UserStory(
        created_by_id=current_user.id,
        requirement_id=payload.requirement_id,
        title=payload.title,
        description=payload.description,
        acceptance_criteria=payload.acceptance_criteria,
        status="draft",
    )

    # I persist the new draft and reload its generated fields.
    db.add(story)
    db.commit()
    db.refresh(story)

    # I retain the authenticated creator for response serialization.
    story.created_by = current_user

    return story


@router.post(
    "/generate",
    response_model=AIUserStoryGenerateResponse,
    status_code=status.HTTP_200_OK,
)
def generate_user_story_draft(
    payload: AIUserStoryGenerateRequest,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(ADMIN, BUSINESS_ANALYST)),
    ],
) -> AIUserStoryGenerateResponse:
    """I generate an AI-assisted user story draft without saving it."""

    # I enforce the public-demo restriction before looking up or changing data.
    if current_user.email.strip().lower() in PUBLIC_DEMO_AI_BLOCKED_EMAILS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=PUBLIC_DEMO_AI_BLOCKED_DETAIL,
        )

    project_id = resolve_project_id_for_requirement(db, payload.requirement_id)

    if project_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found.",
        )

    # I lock and verify the project in a short transaction before generation.
    lock_writable_project(db, project_id)

    # I retrieve the requirement after taking the project lock.
    requirement = db.get(Requirement, payload.requirement_id)

    if requirement is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found.",
        )

    # I release the project lock before invoking the external AI provider.
    db.commit()

    try:
        # I generate a draft using the requirement details.
        generated_story = generate_user_story(
            requirement_title=requirement.title,
            requirement_description=requirement.description,
            requirement_priority=requirement.priority,
        )

    except AIGenerationError as exc:
        # I return a controlled error if the AI service is unavailable.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI user story generation is currently unavailable.",
        ) from exc

    project_id = resolve_project_id_for_requirement(db, payload.requirement_id)

    if project_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requirement not found.",
        )

    # I re-lock and verify the project after generation before responding.
    lock_writable_project(db, project_id)
    db.commit()

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
    dependencies=[
        Depends(require_roles(ADMIN, BUSINESS_ANALYST, REVIEWER))
    ],
)
def get_user_story(
    story_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> UserStory:
    """I return a user story by its unique identifier."""

    # I retrieve the requested user story.
    story = db.scalar(
        select(UserStory)
        .options(selectinload(UserStory.created_by))
        .where(UserStory.id == story_id)
    )

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Story not found.",
        )

    return story


@router.patch(
    "/{story_id}",
    response_model=UserStoryResponse,
    dependencies=[
        Depends(require_roles(ADMIN, BUSINESS_ANALYST))
    ],
)
def update_user_story(
    story_id: UUID,
    payload: UserStoryUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> UserStory:
    """I update user stories while protecting approval decisions."""

    project_id = resolve_project_id_for_user_story(db, story_id)

    if project_id is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Story not found.",
        )

    # I lock and verify the parent project before retrieving the user story.
    lock_writable_project(db, project_id)

    # I verify that the requested user story still exists.
    story = db.get(UserStory, story_id)

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Story not found.",
        )

    # I extract only the fields explicitly provided in the request.
    update_data = payload.model_dump(
        exclude_unset=True,
        mode="json",
    )

    current_status = story.status
    requested_status = update_data.get("status")

    # I prevent any modification to an approved user story.
    if current_status == "approved":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Approved User Stories cannot be modified.",
        )

    # I validate status transitions before applying updates.
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

    # I reserve approval and rejection for audited approval endpoints.
    if requested_status in {"approved", "rejected"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Approval and rejection must use the "
                "dedicated User Story approval endpoints."
            ),
        )

    # I apply only the requested and validated changes.
    for field_name, value in update_data.items():
        setattr(story, field_name, value)

    # I persist the changes and refresh the user story.
    db.commit()
    db.refresh(story)

    return db.scalar(
        select(UserStory)
        .options(selectinload(UserStory.created_by))
        .where(UserStory.id == story_id)
    ) or story
