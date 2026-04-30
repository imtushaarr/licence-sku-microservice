"""Validation Engine - Fast license validation."""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session

from src.models import License, SKU, LicenseStatusEnum, ValidationToken
from src.redis_client import RedisCache
from src.utils.auth import verify_validation_token, create_validation_token
from src.schemas import ValidationResponse, Entitlement, SeatInfo

logger = logging.getLogger(__name__)


class ValidationEngine:
    """Engine for validating licenses."""

    @staticmethod
    async def validate_license(
        db: Session, license_key: str, offline_token: Optional[str] = None
    ) -> Optional[ValidationResponse]:
        """Validate a license."""
        
        # Try offline validation first
        if offline_token:
            token_data = verify_validation_token(offline_token)
            if token_data:
                logger.info(f"Offline validation for license {license_key}")
                return ValidationEngine._build_validation_response(
                    token_data, offline=True
                )

        # Online validation
        license = db.query(License).filter(
            License.license_key == license_key
        ).first()

        if not license:
            logger.warning(f"License not found: {license_key}")
            return ValidationResponse(
                valid=False,
                license_key=license_key,
                customer_id="unknown",
                status=LicenseStatusEnum.REVOKED,
                message="License not found",
                entitlements=[],
                offline_validation=False,
            )

        # Check cache first
        cache_key = f"validation:{license_key}"
        cached_response = await RedisCache.get(cache_key)
        if cached_response:
            logger.debug(f"Cache hit for license {license_key}")
            return ValidationResponse(**cached_response)

        # Validate license
        response = ValidationEngine._validate_license_logic(db, license)

        # Cache the response
        await RedisCache.set(
            cache_key,
            response.dict(),
            ttl=300,  # 5 minutes
        )

        logger.info(f"Validated license {license_key}: {response.valid}")
        return response

    @staticmethod
    def _validate_license_logic(db: Session, license: License) -> ValidationResponse:
        """Logic for validating a license."""
        
        # Check status
        if license.status == LicenseStatusEnum.REVOKED:
            return ValidationResponse(
                valid=False,
                license_key=license.license_key,
                customer_id=license.customer_id,
                status=license.status,
                message=f"License revoked: {license.revoke_reason}",
                entitlements=[],
                offline_validation=False,
            )

        # Check expiry
        if license.status == LicenseStatusEnum.EXPIRED or (
            license.expires_at and license.expires_at < datetime.utcnow()
        ):
            return ValidationResponse(
                valid=False,
                license_key=license.license_key,
                customer_id=license.customer_id,
                status=LicenseStatusEnum.EXPIRED,
                expires_at=license.expires_at,
                message="License expired",
                entitlements=[],
                offline_validation=False,
            )

        # Get SKU details
        sku = db.query(SKU).filter(SKU.id == license.sku_id).first()
        if not sku:
            return ValidationResponse(
                valid=False,
                license_key=license.license_key,
                customer_id=license.customer_id,
                status=license.status,
                message="SKU not found",
                entitlements=[],
                offline_validation=False,
            )

        # Build entitlements from features
        entitlements = [
            Entitlement(
                name=feature_name,
                enabled=enabled,
                details={"tier": sku.tier},
            )
            for feature_name, enabled in sku.features.items()
        ]

        # Build seat info
        seats = None
        if sku.max_seats:
            seats = SeatInfo(
                max_seats=sku.max_seats,
                current_used=license.current_seats_used,
                available=sku.max_seats - license.current_seats_used,
                assignments=license.seat_assignments,
            )

        return ValidationResponse(
            valid=True,
            license_key=license.license_key,
            customer_id=license.customer_id,
            status=license.status,
            expires_at=license.expires_at,
            entitlements=entitlements,
            seats=seats,
            offline_validation=False,
        )

    @staticmethod
    def _build_validation_response(
        token_data: Dict[str, Any], offline: bool = False
    ) -> ValidationResponse:
        """Build validation response from token data."""
        
        entitlements = [
            Entitlement(**ent) for ent in token_data.get("entitlements", [])
        ]

        return ValidationResponse(
            valid=True,
            license_key=token_data.get("license_key", ""),
            customer_id=token_data.get("customer_id", ""),
            status=LicenseStatusEnum(token_data.get("status", "active")),
            expires_at=token_data.get("expires_at"),
            entitlements=entitlements,
            offline_validation=offline,
        )

    @staticmethod
    async def create_offline_token(
        db: Session, license_id: UUID
    ) -> Optional[str]:
        """Create an offline validation token."""
        
        license = db.query(License).filter(License.id == license_id).first()
        if not license:
            return None

        # Check if valid
        if license.status != LicenseStatusEnum.ACTIVE:
            return None

        if license.expires_at and license.expires_at < datetime.utcnow():
            return None

        # Get SKU
        sku = db.query(SKU).filter(SKU.id == license.sku_id).first()
        if not sku:
            return None

        # Build entitlements
        entitlements = [
            {"name": name, "enabled": enabled}
            for name, enabled in sku.features.items()
        ]

        # Create token payload
        token_payload = {
            "license_key": license.license_key,
            "customer_id": license.customer_id,
            "status": license.status.value,
            "expires_at": license.expires_at.isoformat() if license.expires_at else None,
            "entitlements": entitlements,
            "seats": {
                "max_seats": sku.max_seats,
                "current_used": license.current_seats_used,
            } if sku.max_seats else None,
        }

        token = create_validation_token(token_payload)

        # Save token to DB
        validation_token = ValidationToken(
            license_id=license_id,
            token=token,
            expires_at=license.expires_at or datetime.utcnow() + timedelta(days=365),
        )
        
        db.add(validation_token)
        db.commit()

        logger.info(f"Created offline token for license {license_id}")
        return token
