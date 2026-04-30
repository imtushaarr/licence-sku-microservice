"""License Service - Manage license lifecycle."""

import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from src.models import License, SKU, LicenseStatusEnum, WebhookEventEnum
from src.schemas import LicenseCreate, LicenseTransfer, LicenseRevoke, LicenseResponse
from src.utils.auth import generate_license_key, create_validation_token
from src.redis_client import RedisCache
from src.webhooks.event_handler import trigger_webhook_event

logger = logging.getLogger(__name__)


class LicenseService:
    """Service for managing licenses."""

    @staticmethod
    def issue_license(db: Session, license_data: LicenseCreate) -> License:
        """Issue a new license."""
        # Verify SKU exists
        sku = db.query(SKU).filter(SKU.id == license_data.sku_id).first()
        if not sku:
            raise ValueError(f"SKU {license_data.sku_id} not found")

        # Generate unique license key
        license_key = generate_license_key()
        while db.query(License).filter(License.license_key == license_key).first():
            license_key = generate_license_key()

        # Calculate expiry
        expires_at = None
        if sku.trial_days > 0:
            expires_at = datetime.utcnow() + timedelta(days=sku.trial_days)

        license = License(
            license_key=license_key,
            product_id=license_data.product_id,
            sku_id=license_data.sku_id,
            customer_id=license_data.customer_id,
            customer_email=license_data.customer_email,
            organization_id=license_data.organization_id,
            expires_at=expires_at,
            metadata_json=license_data.metadata,
            notes=license_data.notes,
        )

        db.add(license)
        db.commit()
        db.refresh(license)

        # Trigger webhook
        trigger_webhook_event(
            db=db,
            product_id=license_data.product_id,
            event_type=WebhookEventEnum.LICENSE_ISSUED,
            license_id=license.id,
            payload={
                "license_id": str(license.id),
                "license_key": license_key,
                "customer_id": license_data.customer_id,
                "customer_email": license_data.customer_email,
                "sku_id": str(license_data.sku_id),
                "expires_at": expires_at.isoformat() if expires_at else None,
            },
        )

        logger.info(f"Issued license {license.id} to {license_data.customer_id}")
        return license

    @staticmethod
    def get_license(db: Session, license_id: UUID) -> Optional[License]:
        """Get license by ID."""
        return db.query(License).filter(License.id == license_id).first()

    @staticmethod
    def get_license_by_key(db: Session, license_key: str) -> Optional[License]:
        """Get license by key."""
        return db.query(License).filter(License.license_key == license_key).first()

    @staticmethod
    def get_customer_licenses(
        db: Session, customer_id: str, product_id: Optional[UUID] = None
    ) -> List[License]:
        """Get all licenses for a customer."""
        query = db.query(License).filter(License.customer_id == customer_id)
        
        if product_id:
            query = query.filter(License.product_id == product_id)
        
        return query.all()

    @staticmethod
    def activate_license(db: Session, license_id: UUID) -> Optional[License]:
        """Activate a license."""
        license = db.query(License).filter(License.id == license_id).first()
        if not license:
            return None

        license.status = LicenseStatusEnum.ACTIVE
        license.activated_at = datetime.utcnow()
        db.commit()
        db.refresh(license)

        trigger_webhook_event(
            db=db,
            product_id=license.product_id,
            event_type=WebhookEventEnum.LICENSE_ACTIVATED,
            license_id=license.id,
            payload={
                "license_id": str(license.id),
                "activated_at": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"Activated license {license_id}")
        return license

    @staticmethod
    async def revoke_license(
        db: Session, license_id: UUID, revoke_data: LicenseRevoke
    ) -> Optional[License]:
        """Revoke a license."""
        license = db.query(License).filter(License.id == license_id).first()
        if not license:
            return None

        license.status = LicenseStatusEnum.REVOKED
        license.revoked_at = datetime.utcnow()
        license.revoke_reason = revoke_data.reason
        db.commit()
        db.refresh(license)

        # Invalidate cached validation tokens
        await RedisCache.delete(f"validation_token:{license.license_key}")

        trigger_webhook_event(
            db=db,
            product_id=license.product_id,
            event_type=WebhookEventEnum.LICENSE_REVOKED,
            license_id=license.id,
            payload={
                "license_id": str(license.id),
                "revoked_at": datetime.utcnow().isoformat(),
                "reason": revoke_data.reason,
            },
        )

        logger.info(f"Revoked license {license_id}: {revoke_data.reason}")
        return license

    @staticmethod
    def transfer_license(
        db: Session, license_id: UUID, transfer_data: LicenseTransfer
    ) -> Optional[License]:
        """Transfer license to another user."""
        license = db.query(License).filter(License.id == license_id).first()
        if not license:
            return None

        old_customer_id = license.customer_id
        license.customer_id = transfer_data.new_customer_id
        license.customer_email = transfer_data.new_customer_email
        license.seat_assignments = {}
        license.current_seats_used = 0
        db.commit()
        db.refresh(license)

        trigger_webhook_event(
            db=db,
            product_id=license.product_id,
            event_type=WebhookEventEnum.LICENSE_TRANSFERRED,
            license_id=license.id,
            payload={
                "license_id": str(license.id),
                "from_customer_id": old_customer_id,
                "to_customer_id": transfer_data.new_customer_id,
                "transferred_at": datetime.utcnow().isoformat(),
            },
        )

        logger.info(f"Transferred license {license_id} from {old_customer_id}")
        return license

    @staticmethod
    def assign_seat(
        db: Session, license_id: UUID, user_email: str
    ) -> Optional[License]:
        """Assign a seat to a user."""
        license = db.query(License).filter(License.id == license_id).first()
        if not license:
            return None

        sku = db.query(SKU).filter(SKU.id == license.sku_id).first()
        
        # Check seat limit
        if sku.max_seats and license.current_seats_used >= sku.max_seats:
            trigger_webhook_event(
                db=db,
                product_id=license.product_id,
                event_type=WebhookEventEnum.LICENSE_SEAT_LIMIT_REACHED,
                license_id=license.id,
                payload={
                    "license_id": str(license.id),
                    "max_seats": sku.max_seats,
                    "current_used": license.current_seats_used,
                },
            )
            raise ValueError("Seat limit reached")

        # Check if already assigned
        if user_email not in license.seat_assignments:
            license.seat_assignments[user_email] = datetime.utcnow().isoformat()
            license.current_seats_used += 1
            db.commit()
            db.refresh(license)

        logger.info(f"Assigned seat to {user_email} on license {license_id}")
        return license

    @staticmethod
    def unassign_seat(db: Session, license_id: UUID, user_email: str) -> Optional[License]:
        """Unassign a seat from a user."""
        license = db.query(License).filter(License.id == license_id).first()
        if not license:
            return None

        if user_email in license.seat_assignments:
            del license.seat_assignments[user_email]
            license.current_seats_used = max(0, license.current_seats_used - 1)
            db.commit()
            db.refresh(license)

        logger.info(f"Unassigned seat from {user_email} on license {license_id}")
        return license

    @staticmethod
    def check_expiry(db: Session) -> None:
        """Check and update expired licenses."""
        now = datetime.utcnow()
        expired_licenses = db.query(License).filter(
            and_(
                License.status == LicenseStatusEnum.ACTIVE,
                License.expires_at <= now,
            )
        ).all()

        for license in expired_licenses:
            license.status = LicenseStatusEnum.EXPIRED
            
            trigger_webhook_event(
                db=db,
                product_id=license.product_id,
                event_type=WebhookEventEnum.LICENSE_EXPIRED,
                license_id=license.id,
                payload={
                    "license_id": str(license.id),
                    "expired_at": now.isoformat(),
                },
            )

        if expired_licenses:
            db.commit()
            logger.info(f"Updated {len(expired_licenses)} expired licenses")
