"""Health check response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SubsystemCheck(BaseModel):
    """Individual subsystem health check result."""

    status: str
    latency_ms: float | None = None
    error: str | None = None


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    checks: dict[str, SubsystemCheck]
    timestamp: datetime

    model_config = ConfigDict(extra="forbid")
