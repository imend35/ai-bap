
"""I manage role-based access permissions for AI BAP."""

from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.models.user import User
from app.security import get_current_user

ADMIN = "admin"
BUSINESS_ANALYST = "business_analyst"
REVIEWER = "reviewer"

VALID_ROLES = frozenset({
    ADMIN,
    BUSINESS_ANALYST,
    REVIEWER,
})


def require_roles(*allowed_roles: str):
    """I restrict access to users with explicitly permitted roles."""

    # I reject invalid role configurations.
    if not allowed_roles:
        raise ValueError("I must specify at least one allowed role.")

    unknown_roles = set(allowed_roles) - VALID_ROLES

    if unknown_roles:
        raise ValueError(
            f"Unknown roles: {sorted(unknown_roles)}"
        )

    async def check_user_role(
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        """I verify that the authenticated user has an allowed role."""

        # I reject users without the required permission.
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action.",
            )

        return current_user

    return check_user_role
