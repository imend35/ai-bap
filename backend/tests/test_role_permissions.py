
"""I test role-based access control for AI BAP."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.role_permissions import (
    ADMIN,
    BUSINESS_ANALYST,
    REVIEWER,
    require_roles,
)


@pytest.mark.anyio
async def test_admin_can_access_approval():
    """I verify that administrators have approval permission."""
    check_permission = require_roles(ADMIN, REVIEWER)
    user = SimpleNamespace(role=ADMIN)

    result = await check_permission(current_user=user)

    assert result is user


@pytest.mark.anyio
async def test_reviewer_can_access_approval():
    """I verify that reviewers have approval permission."""
    check_permission = require_roles(ADMIN, REVIEWER)
    user = SimpleNamespace(role=REVIEWER)

    result = await check_permission(current_user=user)

    assert result is user


@pytest.mark.anyio
async def test_business_analyst_cannot_approve():
    """I verify that business analysts cannot approve user stories."""
    check_permission = require_roles(ADMIN, REVIEWER)
    user = SimpleNamespace(role=BUSINESS_ANALYST)

    with pytest.raises(HTTPException) as exc_info:
        await check_permission(current_user=user)

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == (
        "You do not have permission to perform this action."
    )


@pytest.mark.anyio
async def test_business_analyst_can_access_allowed_operation():
    """I verify that business analysts can access permitted operations."""
    check_permission = require_roles(ADMIN, BUSINESS_ANALYST)
    user = SimpleNamespace(role=BUSINESS_ANALYST)

    result = await check_permission(current_user=user)

    assert result is user


def test_empty_allowed_roles_are_rejected():
    """I reject permission rules without any allowed roles."""
    with pytest.raises(ValueError, match="at least one allowed role"):
        require_roles()


def test_unknown_role_is_rejected():
    """I reject permission rules containing an unknown role."""
    with pytest.raises(ValueError, match="Unknown roles"):
        require_roles("super_admin")


@pytest.mark.anyio
async def test_unrecognized_user_role_is_denied():
    """I reject users whose roles are not explicitly permitted."""
    check_permission = require_roles(ADMIN, REVIEWER)
    user = SimpleNamespace(role="unknown_role")

    with pytest.raises(HTTPException) as exc_info:
        await check_permission(current_user=user)

    assert exc_info.value.status_code == 403
