
"""I initialize the AI BAP FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers.admin_users import router as admin_users_router
from app.routers.auth import router as auth_router
from app.routers.projects import router as projects_router
from app.routers.requirements import router as requirements_router
from app.routers.sprints import router as sprints_router
from app.routers.tasks import router as tasks_router
from app.routers.user_stories import router as user_stories_router
from app.routers.user_story_approvals import (
    router as user_story_approvals_router,
)

app = FastAPI(
    title="AI BAP API",
    description="AI-Powered Business Analysis Platform",
    version="1.0.0",
)

# I configure cross-origin access for approved frontend addresses.
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/api/v1/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """I return the current API application health status."""
    return {"status": "healthy"}


# I register the authentication endpoints.
app.include_router(auth_router)

# I register administrator-only user-management read endpoints.
app.include_router(admin_users_router)

# I register the existing business analysis endpoints.
app.include_router(projects_router)
app.include_router(requirements_router)
app.include_router(user_stories_router)
app.include_router(tasks_router)
app.include_router(sprints_router)

# I register JWT-protected approval and rejection endpoints.
app.include_router(user_story_approvals_router)
