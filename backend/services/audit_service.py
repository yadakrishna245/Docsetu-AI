"""
DocSetu AI - Audit Logging Service
Records security-relevant events for compliance and monitoring.
"""

import logging
import json
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from models.database import AuditLog


class AuditService:
    """Service for recording audit trail events."""

    def __init__(self, db: Session):
        self.db = db
        self.logger = logging.getLogger('docsetu.audit')

    async def log_event(
        self,
        event_type: str,      # e.g. 'auth.login', 'auth.register', 'admin.role_change'
        actor_id: Optional[str],
        actor_email: Optional[str],
        ip_address: Optional[str],
        details: Optional[dict] = None,
        resource_type: Optional[str] = None,  # 'user', 'document', 'subscription'
        resource_id: Optional[str] = None,
        status: str = 'success'  # 'success' or 'failure'
    ):
        """
        Log a security-relevant event to the database and structured logger.

        Args:
            event_type: Category of event (e.g. 'auth.login_success', 'admin.role_change').
            actor_id: ID of the user performing the action.
            actor_email: Email of the user performing the action.
            ip_address: IP address of the request origin.
            details: Additional context as a dictionary.
            resource_type: Type of resource affected ('user', 'document', 'subscription').
            resource_id: ID of the affected resource.
            status: Outcome of the event ('success' or 'failure').
        """
        # Save to database
        entry = AuditLog(
            event_type=event_type,
            actor_id=actor_id,
            actor_email=actor_email,
            ip_address=ip_address,
            details=details,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
        )
        self.db.add(entry)
        self.db.commit()

        # Also log to structured logger
        self.logger.info(json.dumps({
            'event': event_type,
            'actor': actor_email,
            'ip': ip_address,
            'resource': f'{resource_type}/{resource_id}' if resource_type else None,
            'status': status,
            'timestamp': datetime.utcnow().isoformat()
        }))
