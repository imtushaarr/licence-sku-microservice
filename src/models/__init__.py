"""SQLAlchemy models for License SKU Microservice."""

from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Boolean, Text, 
    ForeignKey, Enum, JSON, TIMESTAMP, func, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timedelta
import uuid
import enum

from src.database import Base


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


class WebhookEventEnum(str, enum.Enum):
    """Webhook event types."""
    LICENSE_ISSUED = "license.issued"
    LICENSE_ACTIVATED = "license.activated"
    LICENSE_EXPIRED = "license.expired"
    LICENSE_REVOKED = "license.revoked"
    LICENSE_TRANSFERRED = "license.transferred"
    LICENSE_SEAT_LIMIT_REACHED = "license.seat_limit_reached"


class Product(Base):
    """Product model - represents a software product."""
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    slug = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(512), nullable=True)
    website_url = Column(String(512), nullable=True)
    created_by = Column(String(255), nullable=False)  # User ID from Clerk
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relationships
    skus = relationship("SKU", back_populates="product", cascade="all, delete-orphan")
    licenses = relationship("License", back_populates="product")
    api_keys = relationship("APIKey", back_populates="product", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_product_slug', 'slug'),
        Index('idx_product_created_by', 'created_by'),
    )


class SKU(Base):
    """SKU model - represents a product tier/variant."""
    __tablename__ = "skus"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    name = Column(String(255), nullable=False)
    tier = Column(Enum(SKUTierEnum), nullable=False)
    description = Column(Text, nullable=True)
    
    # Pricing
    monthly_price = Column(Float, nullable=False, default=0)
    annual_price = Column(Float, nullable=False, default=0)
    trial_days = Column(Integer, nullable=False, default=0)
    
    # Features and limits
    max_seats = Column(Integer, nullable=True)  # NULL = unlimited
    features = Column(JSONB, nullable=False, default={})  # { "feature_name": bool }
    rate_limit = Column(Integer, nullable=True)  # Requests per hour
    storage_gb = Column(Integer, nullable=True)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relationships
    product = relationship("Product", back_populates="skus")
    licenses = relationship("License", back_populates="sku")

    __table_args__ = (
        Index('idx_sku_product_id', 'product_id'),
        Index('idx_sku_tier', 'tier'),
    )


class License(Base):
    """License model - represents an issued license."""
    __tablename__ = "licenses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_key = Column(String(64), nullable=False, unique=True)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    sku_id = Column(UUID(as_uuid=True), ForeignKey("skus.id"), nullable=False)
    
    # License holder info
    customer_id = Column(String(255), nullable=False)  # Clerk user ID or custom ID
    customer_email = Column(String(255), nullable=False)
    organization_id = Column(String(255), nullable=True)
    
    # Status and dates
    status = Column(Enum(LicenseStatusEnum), default=LicenseStatusEnum.ACTIVE)
    issued_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    activated_at = Column(TIMESTAMP(timezone=True), nullable=True)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)
    revoked_at = Column(TIMESTAMP(timezone=True), nullable=True)
    revoke_reason = Column(Text, nullable=True)
    
    # Seats
    current_seats_used = Column(Integer, default=0)
    seat_assignments = Column(JSONB, default={})  # { "user_email": "assigned_date" }
    
    # Metadata
    metadata_json = Column("metadata", JSONB, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), onupdate=func.now())

    # Relationships
    product = relationship("Product", back_populates="licenses")
    sku = relationship("SKU", back_populates="licenses")
    validation_tokens = relationship("ValidationToken", back_populates="license", cascade="all, delete-orphan")

    __table_args__ = (
        Index('idx_license_key', 'license_key'),
        Index('idx_license_customer_id', 'customer_id'),
        Index('idx_license_product_id', 'product_id'),
        Index('idx_license_status', 'status'),
        Index('idx_license_expires_at', 'expires_at'),
    )


class ValidationToken(Base):
    """Signed validation token for offline license validation."""
    __tablename__ = "validation_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    license_id = Column(UUID(as_uuid=True), ForeignKey("licenses.id"), nullable=False)
    token = Column(Text, nullable=False, unique=True)
    
    # Token metadata
    signed_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    revoked_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Relationships
    license = relationship("License", back_populates="validation_tokens")

    __table_args__ = (
        Index('idx_validation_token_license_id', 'license_id'),
        Index('idx_validation_token_expires_at', 'expires_at'),
    )


class APIKey(Base):
    """API Key for service authentication."""
    __tablename__ = "api_keys"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    key = Column(String(64), nullable=False, unique=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Permissions
    permissions = Column(JSONB, nullable=False, default={})
    
    # Status
    is_active = Column(Boolean, default=True)
    last_used_at = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Relationships
    product = relationship("Product", back_populates="api_keys")

    __table_args__ = (
        Index('idx_api_key_key', 'key'),
        Index('idx_api_key_product_id', 'product_id'),
    )


class WebhookEvent(Base):
    """Webhook event log."""
    __tablename__ = "webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    license_id = Column(UUID(as_uuid=True), ForeignKey("licenses.id"), nullable=True)
    event_type = Column(Enum(WebhookEventEnum), nullable=False)
    
    # Payload and status
    payload = Column(JSONB, nullable=False)
    status = Column(String(50), default="pending")  # pending, sent, failed
    retry_count = Column(Integer, default=0)
    last_retry_at = Column(TIMESTAMP(timezone=True), nullable=True)
    next_retry_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    sent_at = Column(TIMESTAMP(timezone=True), nullable=True)

    __table_args__ = (
        Index('idx_webhook_event_product_id', 'product_id'),
        Index('idx_webhook_event_type', 'event_type'),
        Index('idx_webhook_event_status', 'status'),
    )


class AuditLog(Base):
    """Audit log for tracking changes."""
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    action = Column(String(255), nullable=False)
    resource_type = Column(String(50), nullable=False)  # license, sku, api_key
    resource_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Details
    actor_id = Column(String(255), nullable=False)  # Clerk user ID
    changes = Column(JSONB, nullable=True)  # { "field": { "old": value, "new": value } }
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)
    
    # Timestamp
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_audit_log_product_id', 'product_id'),
        Index('idx_audit_log_resource_id', 'resource_id'),
        Index('idx_audit_log_action', 'action'),
    )


class RateLimitState(Base):
    """Rate limit state tracking."""
    __tablename__ = "rate_limit_state"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    api_key = Column(String(64), ForeignKey("api_keys.key"), nullable=False, unique=True)
    requests_count = Column(Integer, default=0)
    window_start = Column(TIMESTAMP(timezone=True), server_default=func.now())
    last_request_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_rate_limit_api_key', 'api_key'),
    )
