"""Middleware implementations."""

import logging
import uuid
from typing import Callable
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time

from src.config import settings
from src.utils.auth import verify_api_key
from src.redis_client import RedisCache

logger = logging.getLogger(__name__)


async def add_request_id_middleware(request: Request, call_next: Callable):
    """Add unique request ID to all requests."""
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


async def rate_limit_middleware(request: Request, call_next: Callable):
    """Rate limiting middleware."""
    # Skip rate limiting for health checks
    if request.url.path == "/health":
        return await call_next(request)

    # Extract API key from header
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Missing API key"},
        )

    # Rate limit key
    rate_limit_key = f"rate_limit:{api_key}"
    
    # Check rate limit
    current_count = await RedisCache.increment(
        rate_limit_key, 1, settings.RATE_LIMIT_PERIOD
    )
    
    if current_count > settings.RATE_LIMIT_REQUESTS:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "Rate limit exceeded",
                "retry_after": settings.RATE_LIMIT_PERIOD,
            },
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_REQUESTS)
    response.headers["X-RateLimit-Remaining"] = str(
        settings.RATE_LIMIT_REQUESTS - current_count
    )
    response.headers["X-RateLimit-Reset"] = str(
        int(time.time()) + settings.RATE_LIMIT_PERIOD
    )
    return response


async def cors_middleware(request: Request, call_next: Callable):
    """CORS middleware."""
    response = await call_next(request)
    origin = request.headers.get("origin")
    
    if origin in settings.CORS_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-API-Key"
    
    return response


async def logging_middleware(request: Request, call_next: Callable):
    """Request/response logging middleware."""
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "method": request.method,
            "path": request.url.path,
        }
    )
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(
        f"Response: {response.status_code}",
        extra={
            "request_id": getattr(request.state, "request_id", "unknown"),
            "status_code": response.status_code,
            "process_time": process_time,
        }
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response
