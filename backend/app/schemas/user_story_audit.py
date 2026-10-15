
"""I define response schemas for user story audit history."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserStoryApprovalAuditResponse(BaseModel):
    """I expose an immutable view of an approval audit record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_story_id: UUID | None
    actor_id: UUID | None
    user_story_id_snapshot: UUID | None
    actor_id_snapshot: UUID | None
    action: str
    previous_status: str
    new_status: str
    created_at: datetime


class UserStoryApprovalAuditListResponse(BaseModel):
    """I return audit history with its total record count."""

    items: list[UserStoryApprovalAuditResponse]
    total: int
