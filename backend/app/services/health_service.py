"""Health check service for monitoring system status."""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import get_redis_client


async def check_health(db: AsyncSession) -> dict[str, Any]:
    """Check health of all critical system components.

    Args:
        db: Async database session for health check.

    Returns:
        Dictionary containing health status and subsystem checks.
    """
    checks: dict[str, dict[str, Any]] = {}
    overall_status = "healthy"

    # Check Database
    try:
        start_time = time.perf_counter()
        await db.execute(text("SELECT 1"))
        db_latency = (time.perf_counter() - start_time) * 1000
        checks["database"] = {
            "status": "ok",
            "latency_ms": round(db_latency, 2),
        }
    except Exception as e:
        checks["database"] = {
            "status": "error",
            "error": str(e),
        }
        overall_status = "unhealthy"

    # Check Redis
    try:
        start_time = time.perf_counter()
        redis_client = await get_redis_client()
        await redis_client.ping()
        redis_latency = (time.perf_counter() - start_time) * 1000
        checks["redis"] = {
            "status": "ok",
            "latency_ms": round(redis_latency, 2),
        }
    except Exception as e:
        checks["redis"] = {
            "status": "error",
            "error": str(e),
        }
        overall_status = "unhealthy"

    # Check Gemini API Key configuration
    if settings.GEMINI_API_KEY and settings.GEMINI_API_KEY.strip():
        checks["gemini_api"] = {
            "status": "ok",
        }
    else:
        checks["gemini_api"] = {
            "status": "not_configured",
        }
        # Note: Not making this unhealthy since it might be intentional
        # during development, but it's worth noting

    return {
        "status": overall_status,
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat(),
    }
