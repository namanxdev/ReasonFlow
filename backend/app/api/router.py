"""Central API router aggregating all sub-routers."""

from fastapi import APIRouter

from app.api.routes import auth, calendar, crm, drafts, emails, metrics, traces

api_router = APIRouter()


@api_router.get("/status", tags=["status"])
async def api_status() -> dict[str, str]:
    """API status endpoint."""
    return {"status": "ok", "version": "0.1.0"}


# Authentication (register/login are public; gmail/* require auth)
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])

# Core email management
api_router.include_router(emails.router, prefix="/emails", tags=["emails"])

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
