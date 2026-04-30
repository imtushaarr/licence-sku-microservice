"""SKU Service - Manage product tiers and variants."""

import logging
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from datetime import datetime

from src.models import SKU, Product, SKUTierEnum
from src.schemas import SKUCreate, SKUUpdate, SKUResponse

logger = logging.getLogger(__name__)


class SKUService:
    """Service for managing SKUs."""

    @staticmethod
    def create_sku(db: Session, sku_data: SKUCreate) -> SKU:
        """Create a new SKU."""
        # Verify product exists
        product = db.query(Product).filter(Product.id == sku_data.product_id).first()
        if not product:
            raise ValueError(f"Product {sku_data.product_id} not found")

        sku = SKU(
            product_id=sku_data.product_id,
            name=sku_data.name,
            tier=sku_data.tier,
            description=sku_data.description,
            monthly_price=sku_data.monthly_price,
            annual_price=sku_data.annual_price,
            trial_days=sku_data.trial_days,
            max_seats=sku_data.max_seats,
            features=sku_data.features,
            rate_limit=sku_data.rate_limit,
            storage_gb=sku_data.storage_gb,
        )
        
        db.add(sku)
        db.commit()
        db.refresh(sku)
        
        logger.info(f"Created SKU {sku.id} for product {sku.product_id}")
        return sku

    @staticmethod
    def get_sku(db: Session, sku_id: UUID) -> Optional[SKU]:
        """Get SKU by ID."""
        return db.query(SKU).filter(SKU.id == sku_id).first()

    @staticmethod
    def get_product_skus(
        db: Session, product_id: UUID, active_only: bool = True
    ) -> List[SKU]:
        """Get all SKUs for a product."""
        query = db.query(SKU).filter(SKU.product_id == product_id)
        
        if active_only:
            query = query.filter(SKU.is_active == True)
        
        return query.all()

    @staticmethod
    def update_sku(db: Session, sku_id: UUID, sku_data: SKUUpdate) -> Optional[SKU]:
        """Update SKU."""
        sku = db.query(SKU).filter(SKU.id == sku_id).first()
        if not sku:
            return None

        update_data = sku_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(sku, field, value)
        
        sku.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(sku)
        
        logger.info(f"Updated SKU {sku_id}")
        return sku

    @staticmethod
    def delete_sku(db: Session, sku_id: UUID) -> bool:
        """Soft delete SKU."""
        sku = db.query(SKU).filter(SKU.id == sku_id).first()
        if not sku:
            return False

        sku.is_active = False
        sku.updated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Deleted SKU {sku_id}")
        return True

    @staticmethod
    def get_sku_by_tier(
        db: Session, product_id: UUID, tier: SKUTierEnum
    ) -> Optional[SKU]:
        """Get SKU by tier."""
        return (
            db.query(SKU)
            .filter(SKU.product_id == product_id, SKU.tier == tier)
            .first()
        )
