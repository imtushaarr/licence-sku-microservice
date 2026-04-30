"""API Key management routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from src.database import get_db
from src.models import Product, APIKey
from src.schemas import APIKeyCreate, APIKeyResponse
from src.utils.auth import generate_api_key, hash_api_key
from src.utils.helpers import log_audit_event

router = APIRouter()


@router.post("/api-keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    api_key_data: APIKeyCreate,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """Create a new API key."""
    
    # Verify product ownership
    product = db.query(Product).filter(Product.id == api_key_data.product_id).first()
    if not product or product.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this product",
        )
    
    # Generate key
    raw_key = generate_api_key()
    hashed_key = hash_api_key(raw_key)
    
    new_api_key = APIKey(
        product_id=api_key_data.product_id,
        key=hashed_key,
        name=api_key_data.name,
        description=api_key_data.description,
        permissions=api_key_data.permissions,
    )
    
    db.add(new_api_key)
    db.commit()
    db.refresh(new_api_key)
    
    log_audit_event(
        action="create",
        resource_type="api_key",
        resource_id=str(new_api_key.id),
        actor_id=current_user_id,
    )
    
    # Return response with raw key (only shown once)
    response = APIKeyResponse.from_orm(new_api_key)
    response.key = raw_key  # Override with raw key for display
    
    return response


@router.get("/api-keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """List API keys for a product."""
    
    # Verify product ownership
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or product.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this product",
        )
    
    api_keys = db.query(APIKey).filter(
        APIKey.product_id == product_id,
        APIKey.is_active == True,
    ).all()
    
    return api_keys


@router.delete("/api-keys/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """Delete API key."""
    
    api_key = db.query(APIKey).filter(APIKey.id == api_key_id).first()
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    
    # Verify product ownership
    product = db.query(Product).filter(Product.id == api_key.product_id).first()
    if not product or product.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this product",
        )
    
    api_key.is_active = False
    db.commit()
    
    log_audit_event(
        action="delete",
        resource_type="api_key",
        resource_id=str(api_key_id),
        actor_id=current_user_id,
    )
