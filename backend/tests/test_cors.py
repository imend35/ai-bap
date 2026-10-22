
"""I test the API cross-origin resource sharing configuration."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_allowed_frontend_origin() -> None:
    """I verify that the approved frontend origin is allowed."""

    # I simulate a preflight request from the approved frontend.
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:5173"
    )


def test_disallowed_frontend_origin() -> None:
    """I verify that an unknown frontend origin is not allowed."""

    # I simulate a preflight request from an unapproved origin.
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "https://untrusted.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_authorization_header_allowed() -> None:
    """I verify that JWT authorization headers are permitted."""

    # I verify that browser preflight requests can request JWT headers.
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        },
    )

    assert response.status_code == 200
    assert (
        "authorization"
        in response.headers["access-control-allow-headers"].lower()
    )
