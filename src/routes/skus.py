"""SKU management routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from src.database import get_db
from src.models import Product
from src.services.sku_service import SKUService
from src.schemas import SKUCreate, SKUUpdate, SKUResponse
from src.utils.helpers import log_audit_event

router = APIRouter()


@router.post("/skus", response_model=SKUResponse, status_code=status.HTTP_201_CREATED)
async def create_sku(
    sku: SKUCreate,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """Create a new SKU."""
    
    # Verify ownership
    product = db.query(Product).filter(Product.id == sku.product_id).first()
    if not product or product.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this product",
        )
    
    try:
        new_sku = SKUService.create_sku(db, sku)
        
        log_audit_event(
            action="create",
            resource_type="sku",
            resource_id=str(new_sku.id),
            actor_id=current_user_id,
        )
        
        return new_sku
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/products/{product_id}/skus", response_model=List[SKUResponse])
async def list_product_skus(
    product_id: UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """List SKUs for a product."""
    
    # Verify ownership
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or product.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this product",
        )
    
    skus = SKUService.get_product_skus(db, product_id, active_only=True)
    return skus[skip : skip + limit]


@router.get("/skus/{sku_id}", response_model=SKUResponse)
async def get_sku(
    sku_id: UUID,
    db: Session = Depends(get_db),
):
    """Get SKU by ID."""
    
    sku = SKUService.get_sku(db, sku_id)
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU not found",
        )
    
    return sku


@router.put("/skus/{sku_id}", response_model=SKUResponse)
async def update_sku(
    sku_id: UUID,
    sku_update: SKUUpdate,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """Update SKU."""
    
    sku = SKUService.get_sku(db, sku_id)
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU not found",
        )
    
    # Verify ownership
    product = db.query(Product).filter(Product.id == sku.product_id).first()
    if not product or product.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this product",
        )
    
    updated_sku = SKUService.update_sku(db, sku_id, sku_update)
    
    log_audit_event(
        action="update",
        resource_type="sku",
        resource_id=str(sku_id),
        actor_id=current_user_id,
        changes=sku_update.dict(exclude_unset=True),
    )
    
    return updated_sku


@router.delete("/skus/{sku_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sku(
    sku_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """Delete SKU."""
    
    sku = SKUService.get_sku(db, sku_id)
    if not sku:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="SKU not found",
        )
    
    # Verify ownership
    product = db.query(Product).filter(Product.id == sku.product_id).first()
    if not product or product.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this product",
        )
    
    SKUService.delete_sku(db, sku_id)
    
    log_audit_event(
        action="delete",
        resource_type="sku",
        resource_id=str(sku_id),
        actor_id=current_user_id,
    )
