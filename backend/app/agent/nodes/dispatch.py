"""Dispatch node — sends the approved response or queues for human review."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import AgentState
from app.core.security import decrypt_oauth_token, encrypt_oauth_token
from app.models.user import User
from app.services.auth_service import refresh_user_gmail_token

logger = logging.getLogger(__name__)


async def check_idempotency(db: AsyncSession, key: str) -> bool:
    """Check if operation with this key was already processed.

    Uses PostgreSQL INSERT ... ON CONFLICT DO NOTHING to atomically check
    and set the idempotency key. If the key already exists, the operation
    is a duplicate.

    Args:
        db: The async database session.
        key: The idempotency key to check.

    Returns:
        True if the operation was already processed (duplicate), False otherwise.
    """
    result = await db.execute(
        text(
            "INSERT INTO idempotency_keys (key) VALUES (:key) "
            "ON CONFLICT (key) DO NOTHING "
            "RETURNING key"
        ),
        {"key": key},
    )
    row = result.fetchone()
    # If row is None, the key already existed (duplicate)
    return row is None


async def _get_user_credentials(
    db: AsyncSession, user_id: uuid.UUID | str
) -> dict[str, Any] | None:
    """Fetch and decrypt user OAuth credentials from the database.

    Refreshes the access token if expired before returning credentials.
    Returns a dict with 'access_token' and optionally 'refresh_token',
    or None if the user has no OAuth credentials.
    """
    if db is None:
        return None

    try:
        user_uuid = uuid.UUID(str(user_id)) if not isinstance(user_id, uuid.UUID) else user_id
        result = await db.execute(select(User).where(User.id == user_uuid))
        user = result.scalar_one_or_none()

        if user is None or not user.oauth_token_encrypted:
            return None

        # Refresh token if needed before using
        await refresh_user_gmail_token(db, user_uuid)

        credentials: dict[str, Any] = {}

        try:
            credentials["access_token"] = decrypt_oauth_token(user.oauth_token_encrypted)
        except ValueError as exc:
            logger.warning("Failed to decrypt access token for user=%s: %s", user_id, exc)
            return None

        if user.oauth_refresh_token_encrypted:
            try:
                credentials["refresh_token"] = decrypt_oauth_token(
                    user.oauth_refresh_token_encrypted
                )
            except ValueError:
                logger.warning("Failed to decrypt refresh token for user=%s", user_id)

        # Define callback to persist refreshed tokens back to database
        def on_token_refresh(updated_creds: dict[str, Any]) -> None:
            """Persist refreshed access token back to user record."""
            new_token = updated_creds.get("access_token")
            if new_token:
                user.oauth_token_encrypted = encrypt_oauth_token(new_token)
                logger.debug("Persisted refreshed Gmail token for user=%s", user_id)

        credentials["_on_token_refresh"] = on_token_refresh

        return credentials
    except Exception as exc:
        logger.warning("Failed to get user credentials for user=%s: %s", user_id, exc)
        return None


async def dispatch_node(
    state: AgentState,
    db: AsyncSession | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    """Dispatch the email response based on the review decision.

    If ``requires_approval`` is False (auto-approved):
      - Sends the ``final_response`` via Gmail using ``send_email`` tool.
      - Updates the ``Email`` record status to ``sent``.

    If ``requires_approval`` is True:
      - Creates a Gmail draft via ``create_draft`` tool.
      - Updates the ``Email`` record status to ``needs_review``.

    Idempotency:
      - If ``idempotency_key`` is provided, checks the database to prevent duplicate sends.
      - Duplicate requests are detected and skipped without sending email.

    Reads:
        ``email``, ``final_response``, ``draft_response``, ``requires_approval``

    Writes:
        ``steps`` — appended step trace entry.
        ``error`` — set on failure.
    """
    step_start = time.monotonic()
    step_name = "dispatch"
    current_steps: list[dict[str, Any]] = list(state.get("steps", []))

    email: dict[str, Any] = state.get("email", {})
    requires_approval: bool = state.get("requires_approval", True)
    final_response: str = state.get("final_response", "")
    draft_response: str = state.get("draft_response", "")

    logger.info(
        "dispatch_node: starting — trace_id=%s requires_approval=%s",
        state.get("trace_id", "unknown"),
        requires_approval,
    )

    action_taken: str = ""
    error_msg: str | None = None

    # Check idempotency key to prevent duplicate sends
    if idempotency_key:
        try:
            if db is not None:
                is_duplicate = await check_idempotency(db, idempotency_key)
                if is_duplicate:
                    logger.info(
                        "dispatch_node: duplicate request detected — idempotency_key=%s",
                        idempotency_key,
                    )
                    latency_ms = (time.monotonic() - step_start) * 1000
                    current_steps.append(
                        {
                            "step": step_name,
                            "action": "duplicate_skipped",
                            "requires_approval": requires_approval,
                            "latency_ms": latency_ms,
                            "idempotency_key": idempotency_key,
                        }
                    )
                    return {
                        "steps": current_steps,
                        "error": None,
                    }
        except Exception as exc:
            logger.warning("dispatch_node: idempotency check failed — %s", exc)
            # Continue with dispatch even if idempotency check fails

    # Get user credentials for Gmail operations
    user_id = email.get("user_id")
    credentials = await _get_user_credentials(db, user_id) if user_id else None

    if not requires_approval:
        # ------------------------------------------------------------------
        # Auto-approved: send immediately via Gmail.
        # ------------------------------------------------------------------
        try:
            from app.integrations.gmail.client import GmailClient  # type: ignore[import]

            if credentials is None:
                raise RuntimeError("User has no valid Gmail OAuth credentials")

            on_refresh = credentials.pop("_on_token_refresh", None)
            client = GmailClient(credentials=credentials, on_token_refresh=on_refresh)
            await client.send_email(
                to=email.get("sender", ""),
                subject=f"Re: {email.get('subject', '')}",
                body=final_response,
                thread_id=email.get("thread_id"),
            )
            action_taken = "sent"
            logger.info("dispatch_node: email sent to %s", email.get("sender"))
        except ImportError:
            # GmailClient not yet implemented — record intent only.
            action_taken = "send_pending"
            logger.warning("dispatch_node: GmailClient not available; marking as send_pending")
        except Exception as exc:
            error_msg = f"dispatch_node send failed: {exc}"
            action_taken = "send_failed"
            logger.exception(error_msg)

        # Update email status in the database.
        new_status = "sent" if action_taken == "sent" else "needs_review"
        await _update_email_status(
            db=db,
            email_id=email.get("id"),
            status=new_status,
            draft_response=final_response,
        )

    else:
        # ------------------------------------------------------------------
        # Requires human review: create a Gmail draft.
        # ------------------------------------------------------------------
        draft_body = draft_response or final_response
        try:
            from app.integrations.gmail.client import GmailClient  # type: ignore[import]

            if credentials is None:
                raise RuntimeError("User has no valid Gmail OAuth credentials")

            on_refresh = credentials.pop("_on_token_refresh", None)
            client = GmailClient(credentials=credentials, on_token_refresh=on_refresh)
            await client.create_draft(
                to=email.get("sender", ""),
                subject=f"Re: {email.get('subject', '')}",
                body=draft_body,
                thread_id=email.get("thread_id"),
            )
            action_taken = "draft_created"
            logger.info("dispatch_node: draft created for human review")
        except ImportError:
            action_taken = "draft_pending"
            logger.warning("dispatch_node: GmailClient not available; marking as draft_pending")
        except Exception as exc:
            error_msg = f"dispatch_node draft creation failed: {exc}"
            action_taken = "draft_failed"
            logger.exception(error_msg)

        await _update_email_status(
            db=db,
            email_id=email.get("id"),
            status="needs_review",
            draft_response=draft_body,
        )

    latency_ms = (time.monotonic() - step_start) * 1000
    step_entry: dict[str, Any] = {
        "step": step_name,
        "action": action_taken,
        "requires_approval": requires_approval,
        "latency_ms": latency_ms,
    }
    if error_msg:
        step_entry["error"] = error_msg
    if idempotency_key:
        step_entry["idempotency_key"] = idempotency_key
    current_steps.append(step_entry)

    logger.info(
        "dispatch_node: done — action=%s latency_ms=%.1f",
        action_taken,
        latency_ms,
    )

    return {
        "steps": current_steps,
        "error": error_msg,
    }


async def _update_email_status(
    db: AsyncSession | None,
    email_id: Any,
    status: str,
    draft_response: str = "",
) -> None:
    """Update the Email record status and draft_response in the database."""
    if db is None or not email_id:
        return

    try:
        from sqlalchemy import select  # noqa: PLC0415

        from app.models.email import Email, EmailStatus  # noqa: PLC0415

        email_uuid = uuid.UUID(str(email_id)) if not isinstance(email_id, uuid.UUID) else email_id
        result = await db.execute(select(Email).where(Email.id == email_uuid))
        email_record = result.scalar_one_or_none()

        if email_record is not None:
            try:
                email_record.status = EmailStatus(status)
            except ValueError:
                email_record.status = EmailStatus.NEEDS_REVIEW

            if draft_response:
                email_record.draft_response = draft_response

            await db.flush()
            logger.debug("dispatch_node: email %s status updated to %s", email_id, status)
    except Exception as exc:
        logger.warning("dispatch_node: failed to update email status — %s", exc)
