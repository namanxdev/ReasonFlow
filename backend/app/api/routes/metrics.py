"""Metrics API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.metrics import IntentMetrics, LatencyMetrics, SummaryStats, ToolMetrics
from app.services import metrics_service

router = APIRouter()


@router.get(
    "/intents",
    response_model=IntentMetrics,
    summary="Intent distribution over time",
)
async def intent_distribution(
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> IntentMetrics:
    """Return the classification distribution for processed emails."""
    data = await metrics_service.get_intent_distribution(db, user.id, start, end)
    return IntentMetrics(**data)


@router.get(
    "/latency",
    response_model=LatencyMetrics,
    summary="Agent response latency statistics",
)
async def latency_metrics(
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> LatencyMetrics:
    """Return percentile latency stats for the agent pipeline."""
    data = await metrics_service.get_latency_metrics(db, user.id, start, end)
    return LatencyMetrics(**data)


@router.get(
    "/tools",
    response_model=ToolMetrics,
    summary="Tool execution success rates",
)
async def tool_metrics(
    start: datetime | None = Query(None),
    end: datetime | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ToolMetrics:
    """Return success rates and latency stats for agent tools."""
    data = await metrics_service.get_tool_metrics(db, user.id, start, end)
    return ToolMetrics(**data)


@router.get(
    "/summary",
    response_model=SummaryStats,
    summary="High-level KPI summary",
)
async def summary_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> SummaryStats:
    """Return high-level KPI summary: total processed, avg response time, approval & review rates.
    """
    data = await metrics_service.get_summary_stats(db, user.id)
    return SummaryStats(**data)
