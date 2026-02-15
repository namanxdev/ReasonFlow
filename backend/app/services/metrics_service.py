"""Metrics aggregation business logic."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_log import AgentLog
from app.models.email import Email
from app.models.tool_execution import ToolExecution

logger = logging.getLogger(__name__)


async def get_intent_distribution(
    db: AsyncSession,
    user_id: uuid.UUID,
    start: datetime | None,
    end: datetime | None,
) -> dict[str, Any]:
    """Return classification counts for emails owned by *user_id*.

    Applies an optional date range filter on ``Email.received_at``.
    Returns a dict matching the ``IntentMetrics`` schema shape.
    """
    query = select(Email.classification, func.count(Email.id)).where(
        Email.user_id == user_id,
        Email.classification.is_not(None),
    )

    if start is not None:
        query = query.where(Email.received_at >= start)
    if end is not None:
        query = query.where(Email.received_at <= end)

    query = query.group_by(Email.classification)
    result = await db.execute(query)
    rows = result.all()

    total = sum(count for _, count in rows)
    buckets = []
    for classification, count in rows:
        percentage = (count / total * 100.0) if total > 0 else 0.0
        buckets.append(
            {
                "classification": classification,
                "count": count,
                "percentage": round(percentage, 2),
            }
        )

    # Sort descending by count for a consistent, readable ordering.
    buckets.sort(key=lambda b: b["count"], reverse=True)

    return {
        "total": total,
        "buckets": buckets,
        "start": start,
        "end": end,
    }


async def get_latency_metrics(
    db: AsyncSession,
    user_id: uuid.UUID,
    start: datetime | None,
    end: datetime | None,
) -> dict[str, Any]:
    """Return agent latency statistics for traces belonging to *user_id*.

    Computes overall and per-step latency percentiles (p50/p90/p99) along with
    mean, min, and max.  Returns a dict matching the ``LatencyMetrics`` schema.
    """
    # Build a subquery: all email ids for this user.
    email_id_subquery = (
        select(Email.id)
        .where(Email.user_id == user_id)
        .scalar_subquery()
    )

    # Fetch all agent log rows (one row per step) for the user's emails.
    log_query = select(AgentLog).where(AgentLog.email_id.in_(email_id_subquery))

    if start is not None:
        log_query = log_query.where(AgentLog.created_at >= start)
    if end is not None:
        log_query = log_query.where(AgentLog.created_at <= end)

    log_result = await db.execute(log_query)
    logs: list[AgentLog] = list(log_result.scalars().all())

    if not logs:
        empty_percentiles = {
            "p50": 0.0,
            "p90": 0.0,
            "p99": 0.0,
            "mean": 0.0,
            "min": 0.0,
            "max": 0.0,
        }
        return {
            "overall": empty_percentiles,
            "by_step": {},
            "sample_count": 0,
            "start": start,
            "end": end,
        }

    # Aggregate per-trace total latency (sum of step latencies per trace_id).
    trace_latencies: dict[uuid.UUID, float] = {}
    step_latencies: dict[str, list[float]] = {}

    for log in logs:
        trace_latencies.setdefault(log.trace_id, 0.0)
        trace_latencies[log.trace_id] += log.latency_ms

        step_latencies.setdefault(log.step_name, [])
        step_latencies[log.step_name].append(log.latency_ms)

    overall_values = list(trace_latencies.values())
    sample_count = len(overall_values)

    overall_percentiles = _compute_percentiles(overall_values)

    by_step: dict[str, dict[str, float]] = {
        step: _compute_percentiles(values)
        for step, values in step_latencies.items()
    }

    return {
        "overall": overall_percentiles,
        "by_step": by_step,
        "sample_count": sample_count,
        "start": start,
        "end": end,
    }


async def get_tool_metrics(
    db: AsyncSession,
    user_id: uuid.UUID,
    start: datetime | None,
    end: datetime | None,
) -> dict[str, Any]:
    """Return tool invocation success/failure rates for *user_id*.

    Returns a dict matching the ``ToolMetrics`` schema shape.
    """
    # Subquery: email ids for the user.
    email_id_subquery = (
        select(Email.id)
        .where(Email.user_id == user_id)
        .scalar_subquery()
    )

    # Subquery: agent_log ids for the user's emails.
    agent_log_id_subquery = (
        select(AgentLog.id)
        .where(AgentLog.email_id.in_(email_id_subquery))
        .scalar_subquery()
    )

    tool_query = select(ToolExecution).where(
        ToolExecution.agent_log_id.in_(agent_log_id_subquery)
    )

    if start is not None:
        tool_query = tool_query.where(ToolExecution.created_at >= start)
    if end is not None:
        tool_query = tool_query.where(ToolExecution.created_at <= end)

    tool_result = await db.execute(tool_query)
    executions: list[ToolExecution] = list(tool_result.scalars().all())

    # Aggregate per tool name.
    tool_stats: dict[str, dict[str, Any]] = {}
    for execution in executions:
        name = execution.tool_name
        if name not in tool_stats:
            tool_stats[name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "latency_sum": 0.0,
            }
        tool_stats[name]["total_calls"] += 1
        if execution.success:
            tool_stats[name]["successful_calls"] += 1
        else:
            tool_stats[name]["failed_calls"] += 1
        tool_stats[name]["latency_sum"] += execution.latency_ms

    tools = []
    for name, stats in tool_stats.items():
        total = stats["total_calls"]
        successful = stats["successful_calls"]
        success_rate = (successful / total) if total > 0 else 0.0
        mean_latency = (stats["latency_sum"] / total) if total > 0 else 0.0
        tools.append(
            {
                "tool_name": name,
                "total_calls": total,
                "successful_calls": successful,
                "failed_calls": stats["failed_calls"],
                "success_rate": round(success_rate, 4),
                "mean_latency_ms": round(mean_latency, 2),
            }
        )

    # Sort by total call volume descending for a consistent ordering.
    tools.sort(key=lambda t: t["total_calls"], reverse=True)

    return {
        "tools": tools,
        "start": start,
        "end": end,
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _compute_percentiles(values: list[float]) -> dict[str, float]:
    """Compute descriptive statistics for a list of latency values.

    Returns a dict with keys: ``p50``, ``p90``, ``p99``, ``mean``, ``min``, ``max``.
    Returns all-zero dict for an empty list.
    """
    if not values:
        return {"p50": 0.0, "p90": 0.0, "p99": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}

    sorted_values = sorted(values)
    n = len(sorted_values)

    def percentile(p: float) -> float:
        # Nearest-rank method.
        rank = max(1, int((p / 100.0) * n))
        return sorted_values[rank - 1]

    return {
        "p50": round(percentile(50), 2),
        "p90": round(percentile(90), 2),
        "p99": round(percentile(99), 2),
        "mean": round(sum(values) / n, 2),
        "min": round(sorted_values[0], 2),
        "max": round(sorted_values[-1], 2),
    }
