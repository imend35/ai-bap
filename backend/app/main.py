
from fastapi import FastAPI

app = FastAPI(
    title="AI BAP API",
    description="AI-Powered Business Analysis Platform",
    version="1.0.0",
)


@app.get("/api/v1/health", tags=["Health"])
def health_check() -> dict[str, str]:
    """Return the current API application health status."""
    return {"status": "healthy"}
