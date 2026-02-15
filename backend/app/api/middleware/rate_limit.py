"""Redis-based sliding-window rate limiter middleware."""

from __future__ import annotations

import logging
import time

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from app.core.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

# Default: 60 requests per minute per user.
RATE_LIMIT_PER_MINUTE: int = getattr(settings, "RATE_LIMIT_PER_MINUTE", 60)
RATE_WINDOW_SECONDS: int = 60


async def rate_limit(
    request: Request,
    redis: Redis = Depends(get_redis),
) -> None:
    """FastAPI dependency that enforces a per-user sliding-window rate limit.

    Usage in a router::

        router = APIRouter(dependencies=[Depends(rate_limit)])

    Raises HTTP 429 if the caller exceeds ``RATE_LIMIT_PER_MINUTE`` requests
    within a 60-second window.
    """
    # Identify caller — prefer authenticated user id, fall back to IP.
    user = getattr(request.state, "user", None)
    if user is not None:
        identifier = f"user:{user.id}"
    else:
        identifier = f"ip:{request.client.host}" if request.client else "ip:unknown"

    key = f"ratelimit:{identifier}"
    now = time.time()
    window_start = now - RATE_WINDOW_SECONDS

    pipe = redis.pipeline()
    # Remove entries outside the window.
    pipe.zremrangebyscore(key, 0, window_start)
    # Count remaining entries.
    pipe.zcard(key)
    # Add current request.
    pipe.zadd(key, {str(now): now})
    # Expire the key after the window to avoid memory leaks.
    pipe.expire(key, RATE_WINDOW_SECONDS + 1)
    results = await pipe.execute()

    request_count: int = results[1]

    if request_count >= RATE_LIMIT_PER_MINUTE:
        retry_after = int(RATE_WINDOW_SECONDS - (now - window_start))
        logger.warning(
            "Rate limit exceeded for %s: %d requests in window",
            identifier,
            request_count,
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(max(retry_after, 1))},
        )
