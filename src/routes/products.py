"""Product management routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from src.database import get_db
from src.models import Product
from src.schemas import ProductCreate, ProductUpdate, ProductResponse
from src.utils.helpers import log_audit_event

router = APIRouter()


@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",  # Would come from Clerk auth
):
    """Create a new product."""
    
    # Check if product slug already exists
    existing = db.query(Product).filter(Product.slug == product.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product slug already exists",
        )
    
    new_product = Product(
        name=product.name,
        slug=product.slug,
        description=product.description,
        logo_url=product.logo_url,
        website_url=product.website_url,
        created_by=current_user_id,
    )
    
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    
    log_audit_event(
        action="create",
        resource_type="product",
        resource_id=str(new_product.id),
        actor_id=current_user_id,
    )
    
    return new_product


@router.get("/products", response_model=List[ProductResponse])
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """List all products for current user."""
    
    products = db.query(Product).filter(
        Product.created_by == current_user_id,
        Product.is_active == True,
    ).offset(skip).limit(limit).all()
    
    return products


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """Get product by ID."""
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.created_by == current_user_id,
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    
    return product


@router.put("/products/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """Update product."""
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.created_by == current_user_id,
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    log_audit_event(
        action="update",
        resource_type="product",
        resource_id=str(product_id),
        actor_id=current_user_id,
        changes=update_data,
    )
    
    return product


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """Delete product (soft delete)."""
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.created_by == current_user_id,
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    
    product.is_active = False
    db.commit()
    
    log_audit_event(
        action="delete",
        resource_type="product",
        resource_id=str(product_id),
        actor_id=current_user_id,
    )
