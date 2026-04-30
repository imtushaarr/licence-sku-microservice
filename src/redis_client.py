"""Redis client configuration and utilities."""

import redis
import json
import logging
from typing import Optional, Any
from src.config import settings

logger = logging.getLogger(__name__)

# Redis client
redis_client = redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_keepalive=True,
)


class RedisCache:
    """Redis cache utility class."""

    @staticmethod
    async def get(key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    @staticmethod
    async def set(key: str, value: Any, ttl: int = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            ttl = ttl or settings.REDIS_CACHE_TTL
            redis_client.setex(
                key, ttl, json.dumps(value, default=str)
            )
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False

    @staticmethod
    async def delete(key: str) -> bool:
        """Delete value from cache."""
        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False

    @staticmethod
    async def exists(key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False

    @staticmethod
    async def increment(key: str, amount: int = 1, ttl: int = 3600) -> int:
        """Increment counter in cache."""
        try:
            pipe = redis_client.pipeline()
            pipe.incr(key, amount)
            pipe.expire(key, ttl)
            result = pipe.execute()
            return result[0]
        except Exception as e:
            logger.error(f"Redis increment error: {e}")
            return 0

    @staticmethod
    async def get_ttl(key: str) -> int:
        """Get TTL for a key."""
        try:
            return redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Redis ttl error: {e}")
            return -1


async def health_check() -> bool:
    """Check Redis health."""
    try:
        redis_client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False
