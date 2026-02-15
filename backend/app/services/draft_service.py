"""Draft management business logic."""

from __future__ import annotations

import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_oauth_token
from app.integrations.gmail.client import GmailClient
from app.models.email import Email, EmailStatus
from app.models.user import User

logger = logging.getLogger(__name__)

# Statuses that indicate a draft is awaiting human review.
_DRAFT_STATUSES = {EmailStatus.DRAFTED, EmailStatus.NEEDS_REVIEW}


async def list_drafts(db: AsyncSession, user_id: uuid.UUID) -> list[Email]:
    """Return all emails with status ``drafted`` or ``needs_review`` for *user_id*."""
    result = await db.execute(
        select(Email)
        .where(
            Email.user_id == user_id,
            Email.status.in_(_DRAFT_STATUSES),
        )
        .order_by(Email.received_at.desc())
    )
    return list(result.scalars().all())


async def approve_draft(
    db: AsyncSession, user: User, email_id: uuid.UUID
) -> dict[str, str]:
    """Send the draft reply via Gmail and mark the email as ``sent``.

    Raises HTTP 404 if the email is not found or not owned by the user.
    Raises HTTP 409 if the email is not in a draft-ready state.
    Raises HTTP 400 if the user has not connected their Gmail account or if
        the email has no draft response to send.
    Raises HTTP 502 on Gmail API errors.
    """
    email = await _get_draft_email(db, user.id, email_id)

    if email.status not in _DRAFT_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email is not in a draft-ready state (current: '{email.status.value}').",
        )

    if not email.draft_response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No draft response content to send.",
        )

    gmail_client = _build_gmail_client(user)

    import httpx

    try:
        await gmail_client.send_email(
            to=email.sender,
            subject=f"Re: {email.subject}",
            body=email.draft_response,
        )
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Gmail send failed for email=%s user=%s: %s %s",
            email_id,
            user.id,
            exc.response.status_code,
            exc.response.text,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send email via Gmail.",
        ) from exc
    except httpx.RequestError as exc:
        logger.error(
            "Network error sending email=%s for user=%s: %s", email_id, user.id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Network error while contacting Gmail.",
        ) from exc

    email.status = EmailStatus.SENT
    await db.flush()

    logger.info("Draft approved and sent: email=%s user=%s", email_id, user.id)
    return {"status": "sent", "email_id": str(email_id)}


async def reject_draft(
    db: AsyncSession, user_id: uuid.UUID, email_id: uuid.UUID
) -> dict[str, str]:
    """Mark the email as ``rejected``, discarding its draft response.

    Raises HTTP 404 if the email is not found or not owned by the user.
    Raises HTTP 409 if the email is not in a draft-ready state.
    """
    email = await _get_draft_email(db, user_id, email_id)

    if email.status not in _DRAFT_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email is not in a draft-ready state (current: '{email.status.value}').",
        )

    email.status = EmailStatus.REJECTED
    await db.flush()

    logger.info("Draft rejected: email=%s user=%s", email_id, user_id)
    return {"status": "rejected", "email_id": str(email_id)}


async def edit_draft(
    db: AsyncSession, user_id: uuid.UUID, email_id: uuid.UUID, new_body: str
) -> Email:
    """Update the ``draft_response`` text of an email record.

    The email status remains unchanged; the caller is expected to approve
    or reject the draft in a subsequent request.

    Raises HTTP 404 if the email is not found or not owned by the user.
    Raises HTTP 409 if the email is not in a draft-ready state.
    """
    email = await _get_draft_email(db, user_id, email_id)

    if email.status not in _DRAFT_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email is not in a draft-ready state (current: '{email.status.value}').",
        )

    email.draft_response = new_body
    await db.flush()
    await db.refresh(email)

    logger.info("Draft edited: email=%s user=%s", email_id, user_id)
    return email


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


async def _get_draft_email(
    db: AsyncSession, user_id: uuid.UUID, email_id: uuid.UUID
) -> Email:
    """Fetch an email by ID, verifying ownership. Raises HTTP 404 if missing."""
    result = await db.execute(
        select(Email).where(Email.id == email_id, Email.user_id == user_id)
    )
    email: Email | None = result.scalars().first()
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found.",
        )
    return email


def _build_gmail_client(user: User) -> GmailClient:
    """Construct a GmailClient from the user's stored, encrypted credentials.

    Raises HTTP 400 if the user has not connected their Gmail account.
    """
    if not user.oauth_token_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gmail account not connected. Complete OAuth flow first.",
        )

    try:
        access_token = decrypt_oauth_token(user.oauth_token_encrypted)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stored Gmail credentials are invalid. Re-connect your account.",
        ) from exc

    credentials: dict[str, str] = {"access_token": access_token}
    if user.oauth_refresh_token_encrypted:
        try:
            credentials["refresh_token"] = decrypt_oauth_token(
                user.oauth_refresh_token_encrypted
            )
        except ValueError:
            logger.warning(
                "Could not decrypt refresh token for user=%s; proceeding without it.",
                user.id,
            )

    return GmailClient(credentials)
