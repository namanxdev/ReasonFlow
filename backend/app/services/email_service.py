"""Email business logic."""

from __future__ import annotations

import logging
import re
import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import EventType, publish_event
from app.core.security import decrypt_oauth_token, encrypt_oauth_token
from app.integrations.gmail.client import GmailClient
from app.llm.client import get_gemini_client
from app.services.auth_service import refresh_user_gmail_token
from app.models.agent_log import AgentLog
from app.models.email import Email, EmailClassification, EmailStatus
from app.models.user import User
from app.schemas.email import EmailFilterParams

logger = logging.getLogger(__name__)


async def list_emails(
    db: AsyncSession,
    user_id: uuid.UUID,
    filters: EmailFilterParams,
) -> tuple[list[Email], int]:
    """Return a paginated, filtered list of emails owned by *user_id*.

    Returns a tuple of ``(items, total)`` where *total* is the count of
    matching rows before pagination is applied.
    """
    query = select(Email).where(Email.user_id == user_id)

    if filters.status is not None:
        query = query.where(Email.status == filters.status)

    if filters.classification is not None:
        query = query.where(Email.classification == filters.classification)

    if filters.search:
        pattern = f"%{filters.search}%"
        query = query.where(
            or_(
                Email.subject.ilike(pattern),
                Email.sender.ilike(pattern),
            )
        )

    # Count total before pagination using SQL-level COUNT.
    count_query = select(func.count()).select_from(Email).where(Email.user_id == user_id)
    if filters.status is not None:
        count_query = count_query.where(Email.status == filters.status)
    if filters.classification is not None:
        count_query = count_query.where(Email.classification == filters.classification)
    if filters.search:
        pattern = f"%{filters.search}%"
        count_query = count_query.where(
            or_(
                Email.subject.ilike(pattern),
                Email.sender.ilike(pattern),
            )
        )

    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Dynamic sorting
    allowed_sort_fields = {
        "received_at": Email.received_at,
        "sender": Email.sender,
        "subject": Email.subject,
        "classification": Email.classification,
        "status": Email.status,
    }
    sort_column = allowed_sort_fields.get(filters.sort_by or "received_at", Email.received_at)
    if filters.sort_order == "asc":
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    offset = (filters.page - 1) * filters.per_page
    query = query.offset(offset).limit(filters.per_page)

    result = await db.execute(query)
    items = list(result.scalars().all())
    return items, total


async def get_email(
    db: AsyncSession, user_id: uuid.UUID, email_id: uuid.UUID
) -> Email:
    """Return a single email by ID, verifying ownership.

    Raises HTTP 404 if the email does not exist or belongs to another user.
    """
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


async def _sync_emails_core(db: AsyncSession, user: User) -> dict[str, int]:
    """Core email sync logic. Raises ValueError/RuntimeError instead of HTTPException.

    Used by both the HTTP endpoint wrapper and the background scheduler.
    """
    if not user.oauth_token_encrypted:
        raise ValueError("Gmail account not connected. Complete OAuth flow first.")

    # Refresh token if needed before using
    await refresh_user_gmail_token(db, user.id)

    try:
        access_token = decrypt_oauth_token(user.oauth_token_encrypted)
    except ValueError as exc:
        raise ValueError("Stored Gmail credentials are invalid. Re-connect your account.") from exc

    credentials: dict[str, Any] = {"access_token": access_token}
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

    # Define callback to persist refreshed tokens to database
    def on_token_refresh(updated_creds: dict[str, Any]) -> None:
        new_token = updated_creds.get("access_token")
        if new_token:
            user.oauth_token_encrypted = encrypt_oauth_token(new_token)
            logger.debug("Persisted refreshed Gmail token for user=%s", user.id)

    gmail_client = GmailClient(credentials, on_token_refresh=on_token_refresh)

    try:
        raw_emails = await gmail_client.fetch_emails()
    except httpx.HTTPStatusError as exc:
        logger.error(
            "Gmail API error for user=%s: %s %s",
            user.id,
            exc.response.status_code,
            exc.response.text,
        )
        raise RuntimeError("Failed to fetch emails from Gmail.") from exc
    except httpx.RequestError as exc:
        logger.error("Network error fetching Gmail emails for user=%s: %s", user.id, exc)
        raise RuntimeError("Network error while contacting Gmail.") from exc

    # Batch fetch all existing gmail_ids in ONE query
    gmail_ids = [raw.get("gmail_id") for raw in raw_emails if raw.get("gmail_id")]
    existing_result = await db.execute(
        select(Email.gmail_id).where(Email.gmail_id.in_(gmail_ids))
    )
    existing_ids = set(existing_result.scalars().all())

    created = 0
    for raw in raw_emails:
        gmail_id: str = raw.get("gmail_id", "")
        if not gmail_id:
            continue
        if gmail_id in existing_ids:
            continue

        received_at_raw = raw.get("received_at")
        if isinstance(received_at_raw, str):
            try:
                received_at = datetime.fromisoformat(received_at_raw)
            except ValueError:
                received_at = datetime.now(UTC)
        elif isinstance(received_at_raw, datetime):
            received_at = received_at_raw
        else:
            received_at = datetime.now(UTC)

        email = Email(
            user_id=user.id,
            gmail_id=gmail_id,
            thread_id=raw.get("thread_id") or None,
            subject=raw.get("subject", ""),
            body=raw.get("body", ""),
            sender=raw.get("sender", ""),
            recipient=raw.get("recipient") or None,
            received_at=received_at,
            status=EmailStatus.PENDING,
        )
        db.add(email)
        created += 1

        await publish_event(
            user_id=user.id,
            event_type=EventType.EMAIL_RECEIVED,
            data={
                "email_id": str(email.id),
                "subject": email.subject,
                "sender": email.sender,
            },
        )

    await db.flush()

    # Auto-populate CRM contacts
    try:
        from app.integrations.crm.factory import get_crm_client

        crm = get_crm_client(db=db, user_id=user.id)
        seen_senders: set[str] = set()
        for raw in raw_emails:
            sender = raw.get("sender", "")
            email_match = re.search(r"<([^>]+)>", sender)
            sender_email = email_match.group(1) if email_match else sender
            sender_email = sender_email.strip().lower()

            if not sender_email or sender_email in seen_senders:
                continue
            seen_senders.add(sender_email)

            existing = await crm.get_contact(sender_email)
            if existing is None:
                # Use enriched contact creation (CRM-4 fix)
                from app.services.contact_enrichment import enrich_contact_data
                
                enriched = enrich_contact_data(
                    sender_email, 
                    sender, 
                    raw.get("body", "")
                )
                
                contact_data = {
                    "name": enriched.get("name", ""),
                    "first_name": enriched.get("first_name", ""),
                    "last_name": enriched.get("last_name", ""),
                    "company": enriched.get("company", ""),
                    "title": enriched.get("title", ""),
                    "notes": "Auto-created from email sync",
                    "tags": ["auto-synced"],
                }
                
                # Add business tag for business emails
                if enriched.get("is_business_email"):
                    contact_data["tags"].append("business")
                
                await crm.update_contact(sender_email, contact_data)
    except Exception as crm_exc:
        logger.warning("CRM auto-populate failed: %s", crm_exc)


def _enrich_and_create_contact(
    crm,
    sender_email: str,
    sender: str,
    body: str = "",
) -> None:
    """Create enriched contact from email data (CRM-4 fix).
    
    Extracts name, company, and title information from the email
    to populate CRM fields more intelligently.
    """
    from app.services.contact_enrichment import enrich_contact_data
    
    enriched = enrich_contact_data(sender_email, sender, body)
    
    contact_data = {
        "name": enriched.get("name", ""),
        "first_name": enriched.get("first_name", ""),
        "last_name": enriched.get("last_name", ""),
        "company": enriched.get("company", ""),
        "title": enriched.get("title", ""),
        "notes": "Auto-created from email sync",
        "tags": ["auto-synced"],
        "is_business_email": enriched.get("is_business_email", False),
    }
    
    # Only add company tag if we detected a business email
    if enriched.get("is_business_email") and enriched.get("company"):
        contact_data["tags"].append("business")
    
    import asyncio
    asyncio.create_task(crm.update_contact(sender_email, contact_data))

    logger.info(
        "Email sync for user=%s: fetched=%d created=%d",
        user.id,
        len(raw_emails),
        created,
    )
    return {"fetched": len(raw_emails), "created": created}


async def sync_emails(db: AsyncSession, user: User) -> dict[str, int]:
    """Fetch new emails from Gmail - HTTP endpoint wrapper.

    Catches ValueError/RuntimeError from core logic and re-raises as HTTPException.
    """
    try:
        return await _sync_emails_core(db, user)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc


async def classify_unclassified_emails(db: AsyncSession, user_id: uuid.UUID) -> dict[str, int]:
    """Classify all emails that don't have a classification yet."""
    result = await db.execute(
        select(Email).where(
            Email.user_id == user_id,
            Email.classification.is_(None),
        )
    )
    emails = list(result.scalars().all())

    if not emails:
        return {"classified": 0, "failed": 0}

    gemini = get_gemini_client()
    classified = 0
    failed = 0

    for email in emails:
        try:
            intent_result = await gemini.classify_intent(
                subject=email.subject,
                body=email.body[:2000],
                sender=email.sender,
            )
            classification_value = intent_result.intent.lower()
            try:
                email.classification = EmailClassification(classification_value)
            except ValueError:
                email.classification = EmailClassification.OTHER
            email.confidence = max(0.0, min(1.0, intent_result.confidence))
            classified += 1

            # Publish event for classification
            await publish_event(
                user_id=user_id,
                event_type=EventType.EMAIL_CLASSIFIED,
                data={
                    "email_id": str(email.id),
                    "classification": email.classification.value,
                    "confidence": email.confidence,
                },
            )
        except Exception as exc:
            logger.warning(
                "Classification failed for email=%s: %s", email.id, exc
            )
            failed += 1

    await db.flush()
    logger.info(
        "Batch classification for user=%s: classified=%d failed=%d",
        user_id, classified, failed,
    )
    return {"classified": classified, "failed": failed}


async def _run_agent_pipeline(email_id: uuid.UUID) -> None:
    """Background task that runs the full LangGraph agent pipeline.

    Opens its own database session since the request session is closed
    by the time background tasks run.
    """
    from app.core.database import async_session_factory

    logger.info("_run_agent_pipeline: starting for email=%s", email_id)

    async with async_session_factory() as db:
        try:
            from app.agent.graph import process_email as agent_process_email

            await agent_process_email(email_id=email_id, db_session=db)
            logger.info("_run_agent_pipeline: completed for email=%s", email_id)
        except BaseException as exc:
            logger.exception(
                "_run_agent_pipeline: failed for email=%s: %s", email_id, exc
            )
            # Ensure email doesn't stay stuck in processing
            try:
                result = await db.execute(
                    select(Email).where(Email.id == email_id)
                )
                stuck_email = result.scalars().first()
                if stuck_email and stuck_email.status == EmailStatus.PROCESSING:
                    stuck_email.status = EmailStatus.NEEDS_REVIEW
                    await db.commit()
                    logger.info(
                        "_run_agent_pipeline: set email=%s to needs_review after failure",
                        email_id,
                    )
            except BaseException as recovery_exc:
                logger.error(
                    "_run_agent_pipeline: recovery failed for email=%s: %s",
                    email_id,
                    recovery_exc,
                )
                await db.rollback()


async def process_email(
    db: AsyncSession, user: User, email_id: uuid.UUID, background_tasks: Any = None
) -> dict[str, str]:
    """Trigger agent processing pipeline for a single email.

    Validates ownership and status, sets the email to ``processing``,
    then kicks off the LangGraph agent pipeline as a background task.

    Raises HTTP 404 if the email is not owned by the user.
    Raises HTTP 409 if the email is already being processed or has been sent.
    """
    result = await db.execute(
        select(Email).where(Email.id == email_id, Email.user_id == user.id)
    )
    email: Email | None = result.scalars().first()
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email not found.",
        )

    if email.status in {EmailStatus.PROCESSING, EmailStatus.SENT}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email is already in '{email.status.value}' state.",
        )

    trace_id = uuid.uuid4()

    # Create the initial agent log entry to record the trace.
    agent_log = AgentLog(
        email_id=email.id,
        trace_id=trace_id,
        step_name="start",
        step_order=0,
        input_state={"email_id": str(email.id), "user_id": str(user.id)},
    )
    db.add(agent_log)

    email.status = EmailStatus.PROCESSING
    await db.commit()

    # Launch the agent pipeline in the background
    if background_tasks is not None:
        background_tasks.add_task(_run_agent_pipeline, email.id)

    logger.info(
        "Processing triggered for email=%s trace_id=%s user=%s",
        email_id,
        trace_id,
        user.id,
    )
    return {"trace_id": str(trace_id), "status": "processing"}
