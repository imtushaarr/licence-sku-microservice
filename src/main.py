"""Main FastAPI application."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import uvicorn

from src.config import settings
from src.database import init_db
from src.redis_client import health_check
from src.middleware.auth import (
    add_request_id_middleware,
    rate_limit_middleware,
    cors_middleware,
    logging_middleware,
)

# Setup logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager."""
    # Startup
    logger.info("Starting License SKU Microservice...")
    init_db()
    redis_ok = await health_check()
    logger.info(f"Redis health check: {'OK' if redis_ok else 'FAILED'}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down License SKU Microservice...")


# Create FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Open-Source License SKU Microservice",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.middleware("http")(add_request_id_middleware)
app.middleware("http")(rate_limit_middleware)
app.middleware("http")(cors_middleware)
app.middleware("http")(logging_middleware)


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Invalid request data",
            "details": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


# Include routers
from src.routes import health, products, skus, licenses, validation, api_keys

app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(products.router, prefix="/api/v1", tags=["Products"])
app.include_router(skus.router, prefix="/api/v1", tags=["SKUs"])
app.include_router(licenses.router, prefix="/api/v1", tags=["Licenses"])
app.include_router(validation.router, prefix="/api/v1", tags=["Validation"])
app.include_router(api_keys.router, prefix="/api/v1", tags=["API Keys"])


if __name__ == "__main__":
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
