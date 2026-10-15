
"""I provide secure API endpoints for task management."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Requirement, Sprint, Task, UserStory
from app.role_permissions import (
    ADMIN,
    BUSINESS_ANALYST,
    REVIEWER,
    require_roles,
)
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)


router = APIRouter(
    prefix="/api/v1/tasks",
    tags=["Tasks"],
)


def validate_task_sprint(
    db: Session,
    story_id: UUID,
    sprint_id: UUID,
) -> None:
    """I verify that a sprint exists and belongs to the task's project."""

    # I reject sprint assignments referencing unknown sprints.
    sprint = db.get(Sprint, sprint_id)

    if sprint is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sprint not found.",
        )

    # I determine the project associated with the selected user story.
    project_id = db.scalar(
        select(Requirement.project_id)
        .join(UserStory, UserStory.requirement_id == Requirement.id)
        .where(UserStory.id == story_id)
    )

    # I prevent tasks from being assigned to another project's sprint.
    if project_id != sprint.project_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sprint must belong to the same project as the task.",
        )


@router.get(
    "",
    response_model=TaskListResponse,
    dependencies=[
        Depends(require_roles(ADMIN, BUSINESS_ANALYST, REVIEWER))
    ],
)
def list_tasks(
    story_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> TaskListResponse:
    """I return a paginated list of tasks for a user story."""

    # I verify that the requested user story exists.
    story = db.get(UserStory, story_id)

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Story not found.",
        )

    # I count the tasks associated with the selected user story.
    total = db.scalar(
        select(func.count())
        .select_from(Task)
        .where(Task.story_id == story_id)
    ) or 0

    # I retrieve tasks using stable ordering and pagination.
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
    dependencies=[
        Depends(require_roles(ADMIN, BUSINESS_ANALYST))
    ],
)
def create_task(
    payload: TaskCreate,
    db: Annotated[Session, Depends(get_db)],
) -> Task:
    """I create a task only for an approved user story."""

    # I verify that the selected user story exists.
    story = db.get(UserStory, payload.story_id)

    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Story not found.",
        )

    # I prevent task creation before the user story is approved.
    if story.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tasks can only be created for approved user stories.",
        )

    # I verify that the selected sprint belongs to the same project.
    if payload.sprint_id is not None:
        validate_task_sprint(
            db=db,
            story_id=payload.story_id,
            sprint_id=payload.sprint_id,
        )

    # I create the task using the validated request data.
    task = Task(
        story_id=payload.story_id,
        sprint_id=payload.sprint_id,
        title=payload.title,
        description=payload.description,
        status=payload.status.value,
    )

    # I persist the new task and reload its database-generated fields.
    db.add(task)
    db.commit()
    db.refresh(task)

    return task


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    dependencies=[
        Depends(require_roles(ADMIN, BUSINESS_ANALYST, REVIEWER))
    ],
)
def get_task(
    task_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> Task:
    """I return a task by its unique identifier."""

    # I retrieve the requested task from the database.
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
    dependencies=[
        Depends(require_roles(ADMIN, BUSINESS_ANALYST))
    ],
)
def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    db: Annotated[Session, Depends(get_db)],
) -> Task:
    """I update task fields while validating sprint assignments."""

    # I verify that the requested task exists.
    task = db.get(Task, task_id)

    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found.",
        )

    # I extract only the fields explicitly provided in the request.
    update_data = payload.model_dump(
        exclude_unset=True,
        mode="json",
    )

    # I verify sprint existence and project consistency when assigned.
    if "sprint_id" in update_data:
        sprint_id = payload.sprint_id

        if sprint_id is not None:
            validate_task_sprint(
                db=db,
                story_id=task.story_id,
                sprint_id=sprint_id,
            )

    # I apply only the requested changes.
    for field_name, value in update_data.items():
        setattr(task, field_name, value)

    # I persist the changes and refresh the updated task.
    db.commit()
    db.refresh(task)

    return task
