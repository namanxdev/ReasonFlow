"""Central API router aggregating all sub-routers."""

from fastapi import APIRouter, Depends

from app.api.middleware.rate_limit import rate_limit
from app.api.routes import (
    auth,
    batch,
    calendar,
    crm,
    drafts,
    emails,
    metrics,
    notifications,
    settings,
    templates,
    traces,
)

api_router = APIRouter(dependencies=[Depends(rate_limit)])

# WebSocket routes need a separate router — they don't have a Request object,
# so the rate_limit dependency (which requires Request) can't be injected.
ws_router = APIRouter()


@api_router.get("/status", tags=["status"])
async def api_status() -> dict[str, str]:
    """API status endpoint."""
    return {"status": "ok", "version": "0.1.0"}


# Authentication (register/login are public; gmail/* require auth)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Core email management
api_router.include_router(emails.router, prefix="/emails", tags=["emails"])

# Batch email operations
api_router.include_router(batch.router, prefix="/emails/batch", tags=["batch"])

# Draft review workflow
api_router.include_router(drafts.router, prefix="/drafts", tags=["drafts"])

# Agent execution traces
api_router.include_router(traces.router, prefix="/traces", tags=["traces"])

# Analytics metrics
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])

# Google Calendar integration
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])

# CRM contacts
api_router.include_router(crm.router, prefix="/crm", tags=["crm"])

# Email templates
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])

# Real-time notifications (WebSocket — mounted on ws_router, no rate_limit)
ws_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])

# Settings/Preferences
api_router.include_router(settings.router, prefix="/settings", tags=["settings"])
