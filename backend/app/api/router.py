"""Central API router aggregating all sub-routers."""

from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/status", tags=["status"])
async def api_status() -> dict[str, str]:
    """API status endpoint."""
    return {"status": "ok", "version": "0.1.0"}
