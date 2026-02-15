"""Email API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
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
)
from app.services import email_service

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
    )
    items, total = await email_service.list_emails(db, user.id, filters)
    return EmailListResponse(
        items=[EmailResponse.model_validate(e) for e in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get(
    "/sync",
    summary="Fetch and store new emails from Gmail",
)
async def sync_emails(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, int]:
    """Trigger a Gmail sync for the authenticated user."""
    return await email_service.sync_emails(db, user)


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
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> EmailProcessResponse:
    """Submit an email to the agent pipeline and return the trace id."""
    result = await email_service.process_email(db, user, email_id)
    return EmailProcessResponse(
        trace_id=result["trace_id"],
        status=result["status"],
    )
