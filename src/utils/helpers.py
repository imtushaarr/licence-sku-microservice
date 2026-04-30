"""Utility functions."""

import logging
from datetime import datetime
from typing import Any, Dict
import json

logger = logging.getLogger(__name__)


def generate_response(
    success: bool,
    data: Any = None,
    message: str = None,
    error: str = None,
    status_code: int = 200,
) -> Dict[str, Any]:
    """Generate standardized response."""
    response = {
        "success": success,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if data is not None:
        response["data"] = data
    
    if message:
        response["message"] = message
    
    if error:
        response["error"] = error
    
    return response


def log_audit_event(
    action: str,
    resource_type: str,
    resource_id: str,
    actor_id: str,
    changes: Dict[str, Any] = None,
    ip_address: str = None,
    user_agent: str = None,
) -> None:
    """Log audit event."""
    logger.info(
        f"Audit: {action} on {resource_type}/{resource_id}",
        extra={
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "actor_id": actor_id,
            "changes": changes,
            "ip_address": ip_address,
            "user_agent": user_agent,
        }
    )
