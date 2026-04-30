"""License validation routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.services.validation_engine import ValidationEngine
from src.schemas import ValidationRequest, ValidationResponse

router = APIRouter()


@router.post("/validate", response_model=ValidationResponse)
async def validate_license(
    request: ValidationRequest,
    db: Session = Depends(get_db),
):
    """Validate a license."""
    
    result = await ValidationEngine.validate_license(
        db=db,
        license_key=request.license_key,
        offline_token=request.offline_token,
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found or validation failed",
        )
    
    return result


@router.post("/validate/offline-token/{license_id}")
async def create_offline_token(
    license_id: str,
    db: Session = Depends(get_db),
):
    """Create an offline validation token."""
    
    from uuid import UUID
    try:
        license_uuid = UUID(license_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid license ID format",
        )
    
    token = await ValidationEngine.create_offline_token(db, license_uuid)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="License not found or cannot create offline token",
        )
    
    return {
        "token": token,
        "expires_in": 86400,  # 24 hours
        "token_type": "offline_validation",
    }
