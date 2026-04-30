"""Pydantic schemas for API requests and responses."""

from pydantic import BaseModel, EmailStr, Field, ConfigDict, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
import enum


class SKUTierEnum(str, enum.Enum):
    """SKU tier levels."""
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class LicenseStatusEnum(str, enum.Enum):
    """License status."""
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    SUSPENDED = "suspended"


# =====================
# Product Schemas
# =====================

class ProductCreate(BaseModel):
    """Create product request."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None


class ProductUpdate(BaseModel):
    """Update product request."""
    name: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    website_url: Optional[str] = None


class ProductResponse(BaseModel):
    """Product response."""
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    logo_url: Optional[str]
    website_url: Optional[str]
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_active: bool

    class Config:
        from_attributes = True


# =====================
# SKU Schemas
# =====================

class FeatureConfig(BaseModel):
    """Feature configuration."""
    name: str
    enabled: bool


class SKUCreate(BaseModel):
    """Create SKU request."""
    product_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    tier: SKUTierEnum
    description: Optional[str] = None
    monthly_price: float = Field(..., ge=0)
    annual_price: float = Field(..., ge=0)
    trial_days: int = Field(default=0, ge=0)
    max_seats: Optional[int] = Field(None, ge=1)
    features: Dict[str, bool] = {}
    rate_limit: Optional[int] = None
    storage_gb: Optional[int] = None


class SKUUpdate(BaseModel):
    """Update SKU request."""
    name: Optional[str] = None
    description: Optional[str] = None
    monthly_price: Optional[float] = Field(None, ge=0)
    annual_price: Optional[float] = Field(None, ge=0)
    trial_days: Optional[int] = Field(None, ge=0)
    max_seats: Optional[int] = Field(None, ge=1)
    features: Optional[Dict[str, bool]] = None
    rate_limit: Optional[int] = None
    storage_gb: Optional[int] = None


class SKUResponse(BaseModel):
    """SKU response."""
    id: UUID
    product_id: UUID
    name: str
    tier: SKUTierEnum
    description: Optional[str]
    monthly_price: float
    annual_price: float
    trial_days: int
    max_seats: Optional[int]
    features: Dict[str, bool]
    rate_limit: Optional[int]
    storage_gb: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================
# License Schemas
# =====================

class LicenseCreate(BaseModel):
    """Create license request."""
    product_id: UUID
    sku_id: UUID
    customer_id: str
    customer_email: EmailStr
    organization_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class LicenseTransfer(BaseModel):
    """Transfer license request."""
    new_customer_id: str
    new_customer_email: EmailStr


class LicenseRevoke(BaseModel):
    """Revoke license request."""
    reason: str = Field(..., min_length=1, max_length=500)


class LicenseSeatAssign(BaseModel):
    """Assign seat request."""
    email: EmailStr


class LicenseResponse(BaseModel):
    """License response."""
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    license_key: str
    product_id: UUID
    sku_id: UUID
    customer_id: str
    customer_email: str
    organization_id: Optional[str]
    status: LicenseStatusEnum
    issued_at: datetime
    activated_at: Optional[datetime]
    expires_at: Optional[datetime]
    revoked_at: Optional[datetime]
    revoke_reason: Optional[str]
    current_seats_used: int
    seat_assignments: Dict[str, str]
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class LicenseListResponse(BaseModel):
    """License list response."""
    total: int
    page: int
    page_size: int
    items: List[LicenseResponse]


# =====================
# Validation Schemas
# =====================

class ValidationRequest(BaseModel):
    """License validation request."""
    license_key: str = Field(..., min_length=1)
    offline_token: Optional[str] = None
    user_id: Optional[str] = None


class Entitlement(BaseModel):
    """Entitlement information."""
    name: str
    enabled: bool
    details: Optional[Dict[str, Any]] = None


class SeatInfo(BaseModel):
    """Seat information."""
    max_seats: Optional[int]
    current_used: int
    available: Optional[int]
    assignments: Dict[str, str]


class ValidationResponse(BaseModel):
    """License validation response."""
    valid: bool
    license_key: str
    customer_id: str
    status: LicenseStatusEnum
    expires_at: Optional[datetime]
    entitlements: List[Entitlement]
    seats: Optional[SeatInfo]
    offline_validation: bool
    message: Optional[str] = None

    class Config:
        from_attributes = True


# =====================
# API Key Schemas
# =====================

class APIKeyCreate(BaseModel):
    """Create API key request."""
    product_id: UUID
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    permissions: Dict[str, List[str]] = Field(
        default={"resources": ["licenses", "skus"], "actions": ["read", "write"]}
    )


class APIKeyResponse(BaseModel):
    """API key response."""
    id: UUID
    product_id: UUID
    key: str
    name: str
    description: Optional[str]
    permissions: Dict[str, List[str]]
    is_active: bool
    last_used_at: Optional[datetime]
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


# =====================
# Health and Status Schemas
# =====================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    timestamp: datetime
    components: Dict[str, str]


class VersionResponse(BaseModel):
    """Version response."""
    version: str
    api_version: str
    build_date: str


# =====================
# Error Schemas
# =====================

class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    message: str
    status_code: int
    timestamp: datetime
    request_id: Optional[str] = None


class ValidationError(BaseModel):
    """Validation error."""
    field: str
    message: str
    value: Optional[Any] = None
