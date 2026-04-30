"""Health check routes."""

from fastapi import APIRouter, Depends
from datetime import datetime
from sqlalchemy.orm import Session

from src.database import get_db
from src.redis_client import health_check
from src.config import settings
from src.schemas import HealthResponse, VersionResponse

router = APIRouter()


@router.get("/health", tags=["Health"])
async def health_check_endpoint(db: Session = Depends(get_db)):
    """Health check endpoint."""
    
    db_ok = True
    redis_ok = await health_check()
    
    return HealthResponse(
        status="healthy" if (db_ok and redis_ok) else "degraded",
        version=settings.API_VERSION,
        timestamp=datetime.utcnow(),
        components={
            "database": "ok" if db_ok else "error",
            "redis": "ok" if redis_ok else "error",
        },
    )


@router.get("/version", tags=["Health"])
async def get_version():
    """Get version information."""
    
    return VersionResponse(
        version=settings.API_VERSION,
        api_version="v1",
        build_date=datetime.utcnow().isoformat(),
    )
