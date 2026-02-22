"""Agent trace retrieval business logic."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.agent_log import AgentLog
from app.models.email import Email

logger = logging.getLogger(__name__)


async def list_traces(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    search: str | None = None,
    status: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """Return a paginated list of recent agent trace summaries for *user_id*.

    Each entry corresponds to one unique ``trace_id`` and aggregates the step
    count and total latency across all steps in that trace.

    Args:
        db: Database session
        user_id: User ID to filter traces for
        limit: Maximum number of traces to return
        offset: Number of traces to skip
        search: Optional search string to filter by email subject
        status: Optional status filter ("completed", "failed", "processing")
    """
    # Resolve email IDs owned by the user.
    email_result = await db.execute(
        select(Email).where(Email.user_id == user_id)
    )
    user_emails: list[Email] = list(email_result.scalars().all())
    if not user_emails:
        return [], 0

    email_map: dict[uuid.UUID, Email] = {e.id: e for e in user_emails}
    email_ids = list(email_map.keys())

    # Fetch all agent log entries for those emails.
    log_result = await db.execute(
        select(AgentLog)
        .where(AgentLog.email_id.in_(email_ids))
        .order_by(AgentLog.created_at.desc())
    )
    logs: list[AgentLog] = list(log_result.scalars().all())

    # Group logs by trace_id.
    traces: dict[uuid.UUID, dict[str, Any]] = {}
    for log in logs:
        tid = log.trace_id
        if tid not in traces:
            email = email_map.get(log.email_id)
            traces[tid] = {
                "trace_id": tid,
                "email_id": log.email_id,
                "email_subject": email.subject if email else "",
                "classification": email.classification if email else None,
                "total_latency_ms": 0.0,
                "step_count": 0,
                "status": "completed",
                "created_at": log.created_at,
            }
        traces[tid]["total_latency_ms"] += log.latency_ms
        traces[tid]["step_count"] += 1
        # Mark the trace as failed if any step recorded an error.
        if log.error_message:
            traces[tid]["status"] = "failed"
        # The created_at for the trace is the latest log timestamp.
        if log.created_at > traces[tid]["created_at"]:
            traces[tid]["created_at"] = log.created_at

    # Keep only the most recent trace per email to avoid duplicate emails in list view.
    latest_trace_by_email: dict[uuid.UUID, dict[str, Any]] = {}
    for trace in traces.values():
        email_id = trace["email_id"]
        current = latest_trace_by_email.get(email_id)
        if current is None or trace["created_at"] > current["created_at"]:
            latest_trace_by_email[email_id] = trace

    # Apply filters.
    filtered_traces = list(latest_trace_by_email.values())

    # Search filter (case-insensitive search on email subject)
    if search:
        search_lower = search.lower()
        filtered_traces = [
            t for t in filtered_traces
            if search_lower in t["email_subject"].lower()
        ]

    # Status filter
    if status:
        filtered_traces = [
            t for t in filtered_traces
            if t["status"].lower() == status.lower()
        ]

    # Sort by created_at descending (most recent first) then paginate.
    sorted_traces = sorted(
        filtered_traces, key=lambda t: t["created_at"], reverse=True
    )
    total_count = len(sorted_traces)
    return sorted_traces[offset : offset + limit], total_count


async def get_trace_detail(
    db: AsyncSession, trace_id: uuid.UUID
) -> dict[str, Any]:
    """Return the full detail for a single trace, including all steps and tool calls.

    Raises HTTP 404 if no agent logs exist for the given trace_id.
    """
    log_result = await db.execute(
        select(AgentLog)
        .where(AgentLog.trace_id == trace_id)
        .options(selectinload(AgentLog.tool_executions))
        .order_by(AgentLog.step_order.asc())
    )
    logs: list[AgentLog] = list(log_result.scalars().all())

    if not logs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Trace not found.",
        )

    # Resolve the associated email from the first log entry.
    first_log = logs[0]
    email_result = await db.execute(
        select(Email).where(Email.id == first_log.email_id)
    )
    email: Email | None = email_result.scalars().first()

    email_summary: dict[str, Any] = {}
    if email is not None:
        email_summary = {
            "id": email.id,
            "subject": email.subject,
            "sender": email.sender,
            "received_at": email.received_at,
            "classification": email.classification,
            "confidence": email.confidence,
        }

    total_latency_ms = sum(log.latency_ms for log in logs)

    steps = []
    for log in logs:
        tool_executions = [
            {
                "id": te.id,
                "tool_name": te.tool_name,
                "params": te.params,
                "result": te.result,
                "success": te.success,
                "error_message": te.error_message,
                "latency_ms": te.latency_ms,
            }
            for te in log.tool_executions
        ]
        steps.append(
            {
                "id": str(log.id),
                "step_name": log.step_name,
                "step_order": log.step_order,
                "input_state": log.input_state,
                "output_state": log.output_state,
                "error_message": log.error_message,
                "latency_ms": log.latency_ms,
                "tool_executions": tool_executions,
            }
        )

    return {
        "trace_id": trace_id,
        "email": email_summary,
        "steps": steps,
        "total_latency_ms": total_latency_ms,
    }
