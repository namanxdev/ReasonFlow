"""Health check service for monitoring system status."""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings


async def check_database(db: AsyncSession) -> dict[str, Any]:
    """Check database connectivity and performance."""
    try:
        start_time = time.perf_counter()
        await db.execute(text("SELECT 1"))
        db_latency = (time.perf_counter() - start_time) * 1000
        
        # Check if we can query actual tables
        start_time = time.perf_counter()
        result = await db.execute(text("SELECT COUNT(*) FROM users"))
        user_count = result.scalar()
        query_latency = (time.perf_counter() - start_time) * 1000
        
        return {
            "status": "ok",
            "latency_ms": round(db_latency, 2),
            "query_latency_ms": round(query_latency, 2),
            "user_count": user_count,
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


async def check_gemini_api() -> dict[str, Any]:
    """Check Gemini API configuration."""
    if not settings.GEMINI_API_KEY or not settings.GEMINI_API_KEY.strip():
        return {
            "status": "not_configured",
            "message": "GEMINI_API_KEY not set",
        }
    
    # Optionally test actual API connectivity
    try:
        # Import here to avoid startup issues
        from app.llm.client import get_gemini_client
        
        start_time = time.perf_counter()
        # We could test with a simple request, but that costs money
        # Instead, just verify client can be instantiated
        client = get_gemini_client()
        init_latency = (time.perf_counter() - start_time) * 1000
        
        return {
            "status": "ok",
            "latency_ms": round(init_latency, 2),
            "message": "API key configured and client initialized",
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


async def check_gmail_oauth() -> dict[str, Any]:
    """Check Gmail OAuth configuration."""
    checks = {}
    
    if settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_ID.strip():
        checks["client_id"] = "configured"
    else:
        checks["client_id"] = "not_configured"
    
    if settings.GMAIL_CLIENT_SECRET and settings.GMAIL_CLIENT_SECRET.strip():
        checks["client_secret"] = "configured"
    else:
        checks["client_secret"] = "not_configured"
    
    if checks["client_id"] == "configured" and checks["client_secret"] == "configured":
        return {
            "status": "ok",
            "checks": checks,
        }
    else:
        return {
            "status": "partial",
            "checks": checks,
            "message": "Gmail OAuth partially configured",
        }


async def check_crm_configuration() -> dict[str, Any]:
    """Check CRM configuration."""
    provider = settings.CRM_PROVIDER.lower()
    
    if provider == "hubspot":
        if settings.HUBSPOT_API_KEY and settings.HUBSPOT_API_KEY.strip():
            return {
                "status": "ok",
                "provider": "hubspot",
                "message": "HubSpot API key configured",
            }
        else:
            return {
                "status": "error",
                "provider": "hubspot",
                "message": "HubSpot API key missing",
            }
    elif provider == "database":
        return {
            "status": "ok",
            "provider": "database",
            "message": "Using database-backed CRM",
        }
    elif provider == "mock":
        return {
            "status": "ok",
            "provider": "mock",
            "message": "Using mock CRM (development mode)",
        }
    else:
        return {
            "status": "unknown",
            "provider": provider,
            "message": f"Unknown CRM provider: {provider}",
        }


async def check_health(db: AsyncSession) -> dict[str, Any]:
    """Check health of all critical system components.

    Performs comprehensive health checks on:
    - Database connectivity and performance
    - Gemini API configuration
    - Gmail OAuth configuration
    - CRM configuration

    Args:
        db: Async database session for health check.

    Returns:
        Dictionary containing health status and subsystem checks.
    """
    checks: dict[str, dict[str, Any]] = {}
    overall_status = "healthy"
    
    # Run all checks concurrently
    results = await asyncio.gather(
        check_database(db),
        check_gemini_api(),
        check_gmail_oauth(),
        check_crm_configuration(),
        return_exceptions=True,
    )
    
    # Process database check
    db_result = results[0]
    if isinstance(db_result, Exception):
        checks["database"] = {"status": "error", "error": str(db_result)}
        overall_status = "unhealthy"
    else:
        checks["database"] = db_result
        if db_result.get("status") == "error":
            overall_status = "unhealthy"
    
    # Process Gemini check
    gemini_result = results[1]
    if isinstance(gemini_result, Exception):
        checks["gemini_api"] = {"status": "error", "error": str(gemini_result)}
    else:
        checks["gemini_api"] = gemini_result
    
    # Process Gmail OAuth check
    gmail_result = results[2]
    if isinstance(gmail_result, Exception):
        checks["gmail_oauth"] = {"status": "error", "error": str(gmail_result)}
    else:
        checks["gmail_oauth"] = gmail_result
    
    # Process CRM check
    crm_result = results[3]
    if isinstance(crm_result, Exception):
        checks["crm"] = {"status": "error", "error": str(crm_result)}
    else:
        checks["crm"] = crm_result
    
    return {
        "status": overall_status,
        "version": "0.1.0",
        "environment": settings.APP_ENV,
        "checks": checks,
        "timestamp": datetime.now(UTC).isoformat(),
    }
