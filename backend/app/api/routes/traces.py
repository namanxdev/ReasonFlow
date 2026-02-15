"""Agent trace API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.trace import (
    TraceDetailResponse,
    TraceListResponse,
    TraceResponse,
)
from app.services import trace_service

router = APIRouter()


@router.get(
    "",
    response_model=TraceListResponse,
    summary="List recent agent execution traces",
)
async def list_traces(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TraceListResponse:
    """Return a paginated list of trace summaries for the current user."""
    rows = await trace_service.list_traces(db, user.id, limit=limit, offset=offset)
    items = [TraceResponse(**row) for row in rows]
    return TraceListResponse(
        items=items,
        total=len(items),
        page=(offset // limit) + 1 if limit else 1,
        per_page=limit,
    )


@router.get(
    "/{trace_id}",
    response_model=TraceDetailResponse,
    summary="Get detailed trace with all steps",
)
async def get_trace(
    trace_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> TraceDetailResponse:
    """Return the full trace including all workflow steps and tool executions."""
    detail = await trace_service.get_trace_detail(db, trace_id)
    return TraceDetailResponse(**detail)
