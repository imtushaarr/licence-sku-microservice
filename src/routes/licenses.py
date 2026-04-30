"""License management routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from src.database import get_db
from src.models import Product, License
from src.services.license_service import LicenseService
from src.schemas import (
    LicenseCreate,
    LicenseTransfer,
    LicenseRevoke,
    LicenseSeatAssign,
    LicenseResponse,
    LicenseListResponse,
)
from src.utils.helpers import log_audit_event

router = APIRouter()


@router.post("/licenses", response_model=LicenseResponse, status_code=status.HTTP_201_CREATED)
async def issue_license(
    license_data: LicenseCreate,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """Issue a new license."""
    
    # Verify product ownership
    product = db.query(Product).filter(Product.id == license_data.product_id).first()
    if not product or product.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to issue licenses for this product",
        )
    
    try:
        license = LicenseService.issue_license(db, license_data)
        
        log_audit_event(
            action="issue",
            resource_type="license",
            resource_id=str(license.id),
            actor_id=current_user_id,
        )
        
        return license
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/licenses", response_model=LicenseListResponse)
async def list_licenses(
    product_id: UUID = Query(...),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: str = Query(None),
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """List licenses for a product."""
    
    # Verify product ownership
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product or product.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view licenses for this product",
        )
    
    query = db.query(License).filter(License.product_id == product_id)
    
    if status:
        query = query.filter(License.status == status)
    
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    
    return LicenseListResponse(
        total=total,
        page=skip // limit,
        page_size=limit,
        items=items,
    )


@router.get("/licenses/{license_id}", response_model=LicenseResponse)
async def get_license(
    license_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """Get license by ID."""
    
    license = LicenseService.get_license(db, license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )
    
    # Verify ownership
    product = db.query(Product).filter(Product.id == license.product_id).first()
    if not product or product.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this license",
        )
    
    return license


@router.post("/licenses/{license_id}/activate", response_model=LicenseResponse)
async def activate_license(
    license_id: UUID,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """Activate a license."""
    
    license = LicenseService.get_license(db, license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )
    
    # Verify ownership
    product = db.query(Product).filter(Product.id == license.product_id).first()
    if not product or product.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this license",
        )
    
    activated = LicenseService.activate_license(db, license_id)
    
    log_audit_event(
        action="activate",
        resource_type="license",
        resource_id=str(license_id),
        actor_id=current_user_id,
    )
    
    return activated


@router.post("/licenses/{license_id}/revoke", response_model=LicenseResponse)
async def revoke_license(
    license_id: UUID,
    revoke_data: LicenseRevoke,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """Revoke a license."""
    
    license = LicenseService.get_license(db, license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )
    
    # Verify ownership
    product = db.query(Product).filter(Product.id == license.product_id).first()
    if not product or product.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this license",
        )
    
    revoked = await LicenseService.revoke_license(db, license_id, revoke_data)
    
    log_audit_event(
        action="revoke",
        resource_type="license",
        resource_id=str(license_id),
        actor_id=current_user_id,
    )
    
    return revoked


@router.post("/licenses/{license_id}/transfer", response_model=LicenseResponse)
async def transfer_license(
    license_id: UUID,
    transfer_data: LicenseTransfer,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """Transfer license to another user."""
    
    license = LicenseService.get_license(db, license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )
    
    # Verify ownership
    product = db.query(Product).filter(Product.id == license.product_id).first()
    if not product or product.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this license",
        )
    
    transferred = LicenseService.transfer_license(db, license_id, transfer_data)
    
    log_audit_event(
        action="transfer",
        resource_type="license",
        resource_id=str(license_id),
        actor_id=current_user_id,
    )
    
    return transferred


@router.post("/licenses/{license_id}/seats/assign")
async def assign_seat(
    license_id: UUID,
    seat_data: LicenseSeatAssign,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """Assign a seat to a user."""
    
    license = LicenseService.get_license(db, license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )
    
    # Verify ownership
    product = db.query(Product).filter(Product.id == license.product_id).first()
    if not product or product.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this license",
        )
    
    try:
        result = LicenseService.assign_seat(db, license_id, seat_data.email)
        return {"success": True, "message": f"Seat assigned to {seat_data.email}"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/licenses/{license_id}/seats/unassign")
async def unassign_seat(
    license_id: UUID,
    seat_data: LicenseSeatAssign,
    db: Session = Depends(get_db),
    current_user_id: str = "user123",
):
    """Unassign a seat from a user."""
    
    license = LicenseService.get_license(db, license_id)
    if not license:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found",
        )
    
    # Verify ownership
    product = db.query(Product).filter(Product.id == license.product_id).first()
    if not product or product.created_by != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to manage this license",
        )
    
    result = LicenseService.unassign_seat(db, license_id, seat_data.email)
    return {"success": True, "message": f"Seat unassigned from {seat_data.email}"}
