"""
DocSetu AI - Role-Based Access Control (RBAC) Utilities
Defines role hierarchy and FastAPI dependencies for route protection.
"""

from fastapi import Depends, HTTPException, status
from models.database import User
from routers.auth import get_current_user


# Role hierarchy: higher index = more permissions
ROLE_HIERARCHY = {
    "viewer": 0,
    "analyst": 1,
    "admin": 2,
}

# Permission matrix (for documentation and future fine-grained checks)
PERMISSIONS = {
    "viewer": [
        "view_own_documents",
        "view_compliance_reports",
    ],
    "analyst": [
        "view_own_documents",
        "view_compliance_reports",
        "upload_documents",
        "run_analysis",
        "run_compliance_checks",
    ],
    "admin": [
        "view_own_documents",
        "view_compliance_reports",
        "upload_documents",
        "run_analysis",
        "run_compliance_checks",
        "manage_users",
        "view_all_documents",
        "delete_any_document",
    ],
}


def get_role_level(role: str) -> int:
    """Get the numeric level for a role. Returns -1 for unknown roles."""
    return ROLE_HIERARCHY.get(role, -1)


def require_role(minimum_role: str):
    """
    FastAPI dependency factory that checks if the current user has at least
    the specified minimum role in the hierarchy.

    Usage:
        @router.get("/endpoint")
        async def endpoint(current_user: User = Depends(require_role("analyst"))):
            ...

    Args:
        minimum_role: The minimum role required (viewer, analyst, or admin).

    Returns:
        A FastAPI dependency function that returns the authenticated user
        if they have sufficient permissions.

    Raises:
        HTTPException 403: If the user's role is below the minimum required.
        ValueError: If the minimum_role is not a valid role.
    """
    if minimum_role not in ROLE_HIERARCHY:
        raise ValueError(f"Invalid role: '{minimum_role}'. Must be one of: {list(ROLE_HIERARCHY.keys())}")

    minimum_level = ROLE_HIERARCHY[minimum_role]

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_level = get_role_level(current_user.role)
        if user_level < minimum_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {minimum_role}, your role: {current_user.role}",
            )
        return current_user

    return role_checker


def require_admin():
    """Shortcut dependency for admin-only routes."""
    return require_role("admin")


def require_analyst():
    """Shortcut dependency for analyst+ routes."""
    return require_role("analyst")
