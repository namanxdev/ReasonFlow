"""Redis client for caching and rate limiting."""

from __future__ import annotations

from typing import Optional

import redis.asyncio as redis

from app.core.config import settings

_redis_client: Optional[redis.Redis] = None


async def get_redis_client() -> redis.Redis:
    """Get or create the Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def close_redis() -> None:
    """Close the Redis connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


async def get_redis() -> redis.Redis:
    """FastAPI dependency for Redis."""
    return await get_redis_client()
