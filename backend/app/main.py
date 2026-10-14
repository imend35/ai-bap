
"""Initialize the AI BAP FastAPI application."""
from fastapi import FastAPI

from app.routers.projects import router as projects_router
from app.routers.requirements import router as requirements_router

app = FastAPI(
    title="AI BAP API",
    description="AI-Powered Business Analysis Platform",
    version="1.0.0",
)


@app.get("/api/v1/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Return the current API application health status."""
    return {"status": "healthy"}


app.router.include_router(projects_router)

app.include_router(requirements_router)
