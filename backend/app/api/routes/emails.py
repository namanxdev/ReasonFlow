"""Email API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.email import EmailClassification, EmailStatus
from app.models.user import User
from app.schemas.email import (
    EmailDetailResponse,
    EmailFilterParams,
    EmailListResponse,
    EmailProcessResponse,
    EmailResponse,
    EmailStatsResponse,
)
from app.services import email_service
from sqlalchemy import func, select
from app.models.email import Email

router = APIRouter()


@router.get(
    "",
    response_model=EmailListResponse,
    summary="List emails with optional filters",
)
async def list_emails(
    status_filter: EmailStatus | None = Query(None, alias="status"),
    classification: EmailClassification | None = Query(None),
    search: str | None = Query(None, max_length=255),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    sort_by: str | None = Query(None),
    sort_order: str | None = Query("desc"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailListResponse:
    """Return a paginated, filtered list of the current user's emails."""
    filters = EmailFilterParams(
        status=status_filter,
        classification=classification,
        search=search,
        page=page,
        per_page=per_page,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    items, total = await email_service.list_emails(db, user.id, filters)
    return EmailListResponse(
        items=[EmailResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post(
    "/sync",
    summary="Fetch and store new emails from Gmail",
)
async def sync_emails(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, int]:
    """Trigger a Gmail sync for the authenticated user."""
    return await email_service.sync_emails(db, user)


@router.post(
    "/classify",
    summary="Classify all unclassified emails",
)
async def classify_emails(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, int]:
    """Trigger classification for all emails without a classification."""
    return await email_service.classify_unclassified_emails(db, user.id)


@router.get(
    "/sync/status",
    summary="Get auto-sync status",
)
async def get_sync_status(
    user: User = Depends(get_current_user),
) -> dict:
    """Return whether auto-sync is active and Gmail is connected."""
    from app.services.scheduler import _scheduler_task
    return {
        "auto_sync_active": _scheduler_task is not None and not _scheduler_task.done(),
        "gmail_connected": user.oauth_token_encrypted is not None,
    }


@router.get(
    "/{email_id}",
    response_model=EmailDetailResponse,
    summary="Get a single email with full details",
)
async def get_email(
    email_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailDetailResponse:
    """Return the full detail of an email owned by the current user."""
    email = await email_service.get_email(db, user.id, email_id)
    return EmailDetailResponse.model_validate(email)


@router.post(
    "/{email_id}/process",
    response_model=EmailProcessResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger agent processing for an email",
)
async def process_email(
    email_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailProcessResponse:
    """Submit an email to the agent pipeline and return the trace id."""
    result = await email_service.process_email(db, user, email_id, background_tasks)
    return EmailProcessResponse(
        trace_id=result["trace_id"],
        status=result["status"],
    )


@router.get("/stats", response_model=EmailStatsResponse, summary="Get email counts by status")
async def get_email_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailStatsResponse:
    """Get email counts by status for the current user."""
    result = await db.execute(
        select(Email.status, func.count())
        .where(Email.user_id == user.id)
        .group_by(Email.status)
    )

    counts = {status: 0 for status in EmailStatus}
    for status, count in result.all():
        counts[status] = count

    return EmailStatsResponse(
        pending=counts.get(EmailStatus.PENDING, 0),
        processing=counts.get(EmailStatus.PROCESSING, 0),
        drafted=counts.get(EmailStatus.DRAFTED, 0),
        needs_review=counts.get(EmailStatus.NEEDS_REVIEW, 0),
        approved=counts.get(EmailStatus.APPROVED, 0),
        sent=counts.get(EmailStatus.SENT, 0),
        rejected=counts.get(EmailStatus.REJECTED, 0),
        total=sum(counts.values()),
    )
