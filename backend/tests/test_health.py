
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_200():
    """Verify that the health endpoint returns HTTP 200."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200


def test_health_endpoint_returns_healthy_status():
    """Verify that the health endpoint returns the expected status."""
    response = client.get("/api/v1/health")

    assert response.json() == {"status": "healthy"}


def test_openapi_metadata():
    """Verify that the generated OpenAPI document contains API metadata."""
    response = client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()

    assert schema["info"]["title"] == "AI BAP API"
    assert schema["info"]["version"] == "1.0.0"
