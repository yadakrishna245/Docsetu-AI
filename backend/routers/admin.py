"""
DocSetu AI - Admin Router
Admin-only endpoints for user management and platform statistics.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from db import get_db
from models.database import User, Document, Analysis, AuditLog
from utils.rbac import require_role, ROLE_HIERARCHY
from services.audit_service import AuditService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# --- Request/Response Models ---

class UserRoleUpdate(BaseModel):
    role: str


class UserStatusUpdate(BaseModel):
    is_active: bool


class AdminUserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str] = None
    organization: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class PlatformStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_documents: int
    total_analyses: int
    users_by_role: dict


# --- Admin Endpoints ---

@router.get("/users", response_model=list[AdminUserResponse])
async def list_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    List all users on the platform. Admin only.

    Args:
        db: Database session.
        current_user: Authenticated admin user.

    Returns:
        List of all users with their details.
    """
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        AdminUserResponse(
            id=u.id,
            email=u.email,
            username=u.username,
            full_name=u.full_name,
            organization=u.organization,
            role=u.role,
            is_active=u.is_active,
            is_verified=u.is_verified,
            created_at=u.created_at.isoformat() if u.created_at else None,
        )
        for u in users
    ]


@router.patch("/users/{user_id}/role", response_model=AdminUserResponse)
async def change_user_role(
    user_id: str,
    payload: UserRoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Change a user's role. Admin only.

    Args:
        user_id: Target user's ID.
        payload: New role to assign.
        request: FastAPI Request object for IP extraction.
        db: Database session.
        current_user: Authenticated admin user.

    Returns:
        Updated user data.
    """
    if payload.role not in ROLE_HIERARCHY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: '{payload.role}'. Must be one of: {list(ROLE_HIERARCHY.keys())}",
        )

    # Prevent admin from demoting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )

    old_role = user.role
    user.role = payload.role
    db.commit()
    db.refresh(user)

    # Audit log: role change
    audit = AuditService(db)
    ip_address = request.client.host if request.client else None
    await audit.log_event(
        event_type='admin.role_change',
        actor_id=current_user.id,
        actor_email=current_user.email,
        ip_address=ip_address,
        details={'old_role': old_role, 'new_role': payload.role, 'target_user': user.email},
        resource_type='user',
        resource_id=user_id,
        status='success',
    )

    logger.info(f"Admin {current_user.email} changed user {user.email} role: {old_role} -> {payload.role}")

    return AdminUserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        organization=user.organization,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.patch("/users/{user_id}/status", response_model=AdminUserResponse)
async def change_user_status(
    user_id: str,
    payload: UserStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Activate or deactivate a user. Admin only.

    Args:
        user_id: Target user's ID.
        payload: New active status.
        request: FastAPI Request object for IP extraction.
        db: Database session.
        current_user: Authenticated admin user.

    Returns:
        Updated user data.
    """
    # Prevent admin from deactivating themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own status",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID '{user_id}' not found",
        )

    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)

    action = "activated" if payload.is_active else "deactivated"

    # Audit log: user deactivation/activation
    if not payload.is_active:
        audit = AuditService(db)
        ip_address = request.client.host if request.client else None
        await audit.log_event(
            event_type='admin.user_deactivate',
            actor_id=current_user.id,
            actor_email=current_user.email,
            ip_address=ip_address,
            details={'target_user': user.email, 'action': action},
            resource_type='user',
            resource_id=user_id,
            status='success',
        )

    logger.info(f"Admin {current_user.email} {action} user {user.email}")

    return AdminUserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        organization=user.organization,
        role=user.role,
        is_active=user.is_active,
        is_verified=user.is_verified,
        created_at=user.created_at.isoformat() if user.created_at else None,
    )


@router.get("/stats", response_model=PlatformStatsResponse)
async def get_platform_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Get platform-wide statistics. Admin only.

    Args:
        db: Database session.
        current_user: Authenticated admin user.

    Returns:
        Platform statistics including user counts, document counts, and analysis counts.
    """
    total_users = db.query(User).count()
    active_users = db.query(User).filter(User.is_active == True).count()
    total_documents = db.query(Document).count()
    total_analyses = db.query(Analysis).count()

    # Count users by role
    users_by_role = {}
    for role in ROLE_HIERARCHY.keys():
        users_by_role[role] = db.query(User).filter(User.role == role).count()

    return PlatformStatsResponse(
        total_users=total_users,
        active_users=active_users,
        total_documents=total_documents,
        total_analyses=total_analyses,
        users_by_role=users_by_role,
    )


# --- Audit Log Response Model ---

class AuditLogResponse(BaseModel):
    id: str
    event_type: str
    actor_id: Optional[str] = None
    actor_email: Optional[str] = None
    ip_address: Optional[str] = None
    details: Optional[dict] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    status: str
    created_at: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedAuditLogsResponse(BaseModel):
    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# --- Audit Log Endpoint ---

@router.get("/audit-logs", response_model=PaginatedAuditLogsResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    actor_email: Optional[str] = Query(None, description="Filter by actor email"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Get paginated audit logs. Admin only.

    Args:
        page: Page number (1-indexed).
        page_size: Number of items per page.
        event_type: Optional filter by event type.
        actor_email: Optional filter by actor email.
        db: Database session.
        current_user: Authenticated admin user.

    Returns:
        Paginated list of audit log entries.
    """
    query = db.query(AuditLog)

    # Apply filters
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)
    if actor_email:
        query = query.filter(AuditLog.actor_email.ilike(f"%{actor_email}%"))

    # Get total count
    total = query.count()

    # Paginate (most recent first)
    offset = (page - 1) * page_size
    logs = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size).all()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size

    return PaginatedAuditLogsResponse(
        items=[
            AuditLogResponse(
                id=log.id,
                event_type=log.event_type,
                actor_id=log.actor_id,
                actor_email=log.actor_email,
                ip_address=log.ip_address,
                details=log.details,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                status=log.status,
                created_at=log.created_at.isoformat() if log.created_at else None,
            )
            for log in logs
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
