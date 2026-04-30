"""Webhook event handling."""

import logging
import json
import asyncio
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import requests

from src.models import WebhookEvent, WebhookEventEnum, Product
from src.config import settings
from src.redis_client import RedisCache

logger = logging.getLogger(__name__)


def trigger_webhook_event(
    db: Session,
    product_id: UUID,
    event_type: WebhookEventEnum,
    payload: Dict[str, Any],
    license_id: Optional[UUID] = None,
) -> None:
    """Trigger a webhook event."""
    
    event = WebhookEvent(
        product_id=product_id,
        license_id=license_id,
        event_type=event_type,
        payload=payload,
        status="pending",
    )
    
    db.add(event)
    db.commit()
    
    logger.info(f"Created webhook event: {event_type.value} for product {product_id}")
    
    # Schedule async sending
    asyncio.create_task(send_webhook_event(db, event.id))


async def send_webhook_event(db: Session, event_id: UUID) -> None:
    """Send webhook event to registered endpoints."""
    
    event = db.query(WebhookEvent).filter(WebhookEvent.id == event_id).first()
    if not event:
        return

    # Get product's webhook endpoints from cache or config
    cache_key = f"webhooks:{event.product_id}"
    endpoints = await RedisCache.get(cache_key)
    
    if not endpoints:
        # Default: could be loaded from product settings
        endpoints = []

    if not endpoints:
        event.status = "skipped"
        db.commit()
        return

    success_count = 0
    for endpoint in endpoints:
        success = await _send_to_endpoint(event, endpoint)
        if success:
            success_count += 1
        else:
            # Schedule retry
            if event.retry_count < settings.WEBHOOK_MAX_RETRIES:
                event.retry_count += 1
                event.next_retry_at = datetime.utcnow() + timedelta(
                    seconds=settings.WEBHOOK_RETRY_DELAY * (2 ** (event.retry_count - 1))
                )
                event.status = "pending"
            else:
                event.status = "failed"

    if success_count == len(endpoints):
        event.status = "sent"
        event.sent_at = datetime.utcnow()
    
    db.commit()


async def _send_to_endpoint(event: WebhookEvent, endpoint: str) -> bool:
    """Send webhook event to a specific endpoint."""
    
    try:
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": event.event_type.value,
            "X-Webhook-Timestamp": datetime.utcnow().isoformat(),
        }
        
        # Add signature for security
        import hmac
        import hashlib
        payload_str = json.dumps(event.payload)
        signature = hmac.new(
            settings.WEBHOOK_SECRET.encode(),
            payload_str.encode(),
            hashlib.sha256,
        ).hexdigest()
        headers["X-Webhook-Signature"] = signature

        response = requests.post(
            endpoint,
            json=event.payload,
            headers=headers,
            timeout=10,
        )
        
        success = 200 <= response.status_code < 300
        logger.info(f"Webhook sent to {endpoint}: {response.status_code}")
        return success
        
    except Exception as e:
        logger.error(f"Failed to send webhook to {endpoint}: {e}")
        return False


async def retry_pending_webhooks(db: Session) -> None:
    """Retry pending webhook events."""
    
    now = datetime.utcnow()
    pending_events = db.query(WebhookEvent).filter(
        WebhookEvent.status == "pending",
        WebhookEvent.next_retry_at <= now,
    ).all()

    for event in pending_events:
        await send_webhook_event(db, event.id)

    logger.info(f"Retried {len(pending_events)} pending webhook events")
