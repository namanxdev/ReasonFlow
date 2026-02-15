"""Draft management API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.draft import DraftEditRequest, DraftListResponse, DraftResponse
from app.services import draft_service

router = APIRouter()


@router.get(
    "",
    response_model=DraftListResponse,
    summary="List drafts awaiting review",
)
async def list_drafts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DraftListResponse:
    """Return all emails in drafted / needs_review status for the current user."""
    items = await draft_service.list_drafts(db, user.id)
    return DraftListResponse(
        items=[DraftResponse.model_validate(e) for e in items],
        total=len(items),
        page=1,
        per_page=len(items) or 20,
    )


@router.post(
    "/{email_id}/approve",
    status_code=status.HTTP_200_OK,
    summary="Approve and send a draft",
)
async def approve_draft(
    email_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Approve a draft, send it via Gmail, and mark the email as sent."""
    return await draft_service.approve_draft(db, user, email_id)


@router.post(
    "/{email_id}/reject",
    status_code=status.HTTP_200_OK,
    summary="Reject a draft",
)
async def reject_draft(
    email_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict[str, str]:
    """Reject a draft and revert the email to pending status."""
    return await draft_service.reject_draft(db, user.id, email_id)


@router.put(
    "/{email_id}",
    response_model=DraftResponse,
    summary="Edit a draft before sending",
)
async def edit_draft(
    email_id: uuid.UUID,
    body: DraftEditRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> DraftResponse:
    """Update the draft content for an email before approval."""
    email = await draft_service.edit_draft(db, user.id, email_id, body.content)
    return DraftResponse.model_validate(email)
