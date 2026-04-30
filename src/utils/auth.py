"""Authentication utilities."""

import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional
import jwt
import logging

from src.config import settings

logger = logging.getLogger(__name__)


def generate_api_key() -> str:
    """Generate a secure API key."""
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """Hash an API key."""
    return hashlib.sha256(api_key.encode()).hexdigest()


def verify_api_key(api_key: str, hashed_key: str) -> bool:
    """Verify an API key against its hash."""
    return hash_api_key(api_key) == hashed_key


def generate_license_key() -> str:
    """Generate a unique license key."""
    # Format: PROD-XXXX-XXXX-XXXX-XXXX
    random_part = secrets.token_hex(8).upper()
    parts = [random_part[i:i+4] for i in range(0, len(random_part), 4)]
    return f"LIC-{'-'.join(parts[:4])}"


def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None


def create_validation_token(license_data: dict) -> str:
    """Create a signed validation token for offline validation."""
    payload = {
        **license_data,
        "exp": datetime.utcnow() + timedelta(seconds=settings.VALIDATION_TOKEN_EXPIRY),
        "iss": "license-sku-service",
    }
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return token


def verify_validation_token(token: str) -> Optional[dict]:
    """Verify a signed validation token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Validation token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid validation token: {e}")
        return None
