"""Configuration module for License SKU Microservice."""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_TITLE: str = "License SKU Microservice"
    API_VERSION: str = "v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Database Configuration
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/licence_sku_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600

    # CORS Configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Authentication
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    CLERK_PUBLISHABLE_KEY: str = ""
    CLERK_SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 1000
    RATE_LIMIT_PERIOD: int = 3600

    # Webhook Configuration
    WEBHOOK_SECRET: str = "your-webhook-secret"
    WEBHOOK_MAX_RETRIES: int = 5
    WEBHOOK_RETRY_DELAY: int = 300

    # Service URLs
    CLERK_AUTH_SERVICE_URL: str = "http://localhost:5173"
    VALIDATION_TOKEN_EXPIRY: int = 86400

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
