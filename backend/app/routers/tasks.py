
"""Provide API endpoints for task management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Task, UserStory
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)
from app.security import verify_demo_token


router = APIRouter(
    prefix="/api/v1/tasks",
    tags=["Tasks"],
    dependencies=[Depends(verify_demo_token)],
)

@router.get("", response_model=TaskListResponse)
def list_tasks(
    story_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TaskListResponse:
    """Return a paginated list of tasks for a user story."""
    story = db.get(UserStory, story_id)

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Story not found.",
        )

    total = db.scalar(
        select(func.count())
        .select_from(Task)
        .where(Task.story_id == story_id)
    ) or 0

    statement = (
        select(Task)
        .where(Task.story_id == story_id)
        .order_by(Task.created_at.desc(), Task.id.desc())
        .limit(limit)
        .offset(offset)
    )

    tasks = db.scalars(statement).all()

    return TaskListResponse(
        items=tasks,
        total=total,
        limit=limit,
        offset=offset,
    )

@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    payload: TaskCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Task:
    """Create a task only for an approved user story."""
    story = db.get(UserStory, payload.story_id)

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Story not found.",
        )

    if story.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tasks can only be created for approved user stories.",
        )

    task = Task(
        story_id=payload.story_id,
        title=payload.title,
        description=payload.description,
        status=payload.status.value,
    )

    db.add(task)
    db.commit()
    db.refresh(task)

    return task

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
)
def get_task(
    task_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Task:
    """Return a single task by its unique identifier."""
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    return task

@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
)
def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Task:
    """Update only the provided fields of an existing task."""
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    update_data = payload.model_dump(
        exclude_unset=True,
        mode="json",
    )

    for field_name, value in update_data.items():
        setattr(task, field_name, value)

    db.commit()
    db.refresh(task)

    return task
