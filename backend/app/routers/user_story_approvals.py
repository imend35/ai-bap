
"""I manage JWT-protected user story approval decisions and audit records."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.database import get_db
from app.models import UserStory, UserStoryApprovalAudit
from app.models.user import User
from app.role_permissions import ADMIN, REVIEWER, require_roles
from app.schemas.user_story import UserStoryResponse
from app.schemas.user_story_audit import UserStoryApprovalAuditListResponse

router = APIRouter(
    prefix="/api/v1/user-stories",
    tags=["User Story Approvals"],
)


@router.post(
    "/{story_id}/approve",
    response_model=UserStoryResponse,
)
def approve_user_story(
    story_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(ADMIN, REVIEWER)),
    ],
) -> UserStory:
    """I approve a reviewed user story and record the decision."""

    # I retrieve and lock the user story to prevent concurrent decisions.
    story = (
        db.query(UserStory)
        .filter(UserStory.id == story_id)
        .with_for_update()
        .one_or_none()
    )

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Story not found.",
        )

    # I require human review before approval.
    if story.status != "in_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only User Stories in review can be approved.",
        )

    # I preserve the previous status for my audit record.
    previous_status = story.status

    # I update the user story status.
    story.status = "approved"

    # I record who approved the user story.
    audit_record = UserStoryApprovalAudit(
        user_story_id=story.id,
        actor_id=current_user.id,
        user_story_id_snapshot=story.id,
        actor_id_snapshot=current_user.id,
        action="approved",
        previous_status=previous_status,
        new_status="approved",
    )

    db.add(audit_record)

    # I commit the status change and audit record atomically.
    db.commit()
    db.refresh(story)

    return db.scalar(
        select(UserStory)
        .options(selectinload(UserStory.created_by))
        .where(UserStory.id == story_id)
    ) or story


@router.post(
    "/{story_id}/reject",
    response_model=UserStoryResponse,
)
def reject_user_story(
    story_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(ADMIN, REVIEWER)),
    ],
) -> UserStory:
    """I reject a reviewed user story and record the decision."""

    # I retrieve and lock the user story to prevent concurrent decisions.
    story = (
        db.query(UserStory)
        .filter(UserStory.id == story_id)
        .with_for_update()
        .one_or_none()
    )

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Story not found.",
        )

    # I require human review before rejection.
    if story.status != "in_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only User Stories in review can be rejected.",
        )

    # I preserve the previous status for my audit record.
    previous_status = story.status

    # I update the user story status.
    story.status = "rejected"

    # I record who rejected the user story.
    audit_record = UserStoryApprovalAudit(
        user_story_id=story.id,
        actor_id=current_user.id,
        user_story_id_snapshot=story.id,
        actor_id_snapshot=current_user.id,
        action="rejected",
        previous_status=previous_status,
        new_status="rejected",
    )

    db.add(audit_record)


    # I commit the status change and audit record atomically.
    db.commit()
    db.refresh(story)

    return db.scalar(
        select(UserStory)
        .options(selectinload(UserStory.created_by))
        .where(UserStory.id == story_id)
    ) or story


@router.get(
    "/{story_id}/audit",
    response_model=UserStoryApprovalAuditListResponse,
)
def get_user_story_audit_history(
    story_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current_user: Annotated[
        User,
        Depends(require_roles(ADMIN, REVIEWER)),
    ],
) -> UserStoryApprovalAuditListResponse:
    """I return the audit history for a user story."""

    # I retrieve the audit records using the immutable story identifier.
    statement = (
        select(UserStoryApprovalAudit)
        .where(
            UserStoryApprovalAudit.user_story_id_snapshot == story_id
        )
        .order_by(
            UserStoryApprovalAudit.created_at.desc(),
            UserStoryApprovalAudit.id.desc(),
        )
    )

    records = db.scalars(statement).all()

    return UserStoryApprovalAuditListResponse(
        items=records,
        total=len(records),
    )
