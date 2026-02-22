"""In-memory sliding-window rate limiter middleware.

Uses a module-level dictionary to track request timestamps per caller.
Suitable for single-server MVP deployments. State resets on server restart.
"""

from __future__ import annotations

import logging
import time

from fastapi import HTTPException, Request, status

from app.core.config import settings

logger = logging.getLogger(__name__)

# Default: 60 requests per minute per user.
RATE_LIMIT_PER_MINUTE: int = getattr(settings, "RATE_LIMIT_PER_MINUTE", 60)
RATE_WINDOW_SECONDS: int = 60

# Stricter limits for auth endpoints
AUTH_RATE_LIMIT_PER_MINUTE: int = 10

# In-memory store: {identifier: [timestamp, ...]}
_request_log: dict[str, list[float]] = {}


async def rate_limit(
    request: Request,
    limit: int = RATE_LIMIT_PER_MINUTE,
) -> None:
    """FastAPI dependency that enforces a per-user sliding-window rate limit.

    Usage in a router::

        router = APIRouter(dependencies=[Depends(rate_limit)])

    Raises HTTP 429 if the caller exceeds ``RATE_LIMIT_PER_MINUTE`` requests
    within a 60-second window.

    Uses in-memory tracking — state resets on server restart.
    """
    # Identify caller — prefer authenticated user id, fall back to IP.
    user = getattr(request.state, "user", None)
    if user is not None:
        identifier = f"user:{user.id}"
    else:
        identifier = f"ip:{request.client.host}" if request.client else "ip:unknown"

    now = time.time()
    window_start = now - RATE_WINDOW_SECONDS

    # Get or create the request log for this identifier
    timestamps = _request_log.get(identifier, [])

    # Remove entries outside the window
    timestamps = [t for t in timestamps if t > window_start]

    if len(timestamps) >= limit:
        retry_after = int(RATE_WINDOW_SECONDS - (now - window_start))
        logger.warning(
            "Rate limit exceeded for %s: %d requests in window",
            identifier,
            len(timestamps),
        )
        # Store cleaned list back before raising
        _request_log[identifier] = timestamps
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": str(max(retry_after, 1))},
        )

    # Add current request timestamp
    timestamps.append(now)
    _request_log[identifier] = timestamps


# Pre-configured rate limiter for auth endpoints (10 req/min)
async def auth_rate_limit(
    request: Request,
) -> None:
    """Stricter rate limiter for authentication endpoints.

    Usage in auth routes:

        @router.post("/login", dependencies=[Depends(auth_rate_limit)])

    Uses in-memory tracking — state resets on server restart.
    """
    await rate_limit(request, limit=AUTH_RATE_LIMIT_PER_MINUTE)
