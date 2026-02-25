"""Batch operation business logic with background task processing.

Uses in-memory storage for batch job state tracking.
Suitable for single-server MVP deployments. State resets on server restart.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime

from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.task_tracker import get_task_tracker
from app.llm.client import get_gemini_client
from app.models.email import Email, EmailClassification, EmailStatus
from app.models.user import User
from app.schemas.batch import BatchJobResponse, BatchStatusResponse

logger = logging.getLogger(__name__)


# In-memory batch job store: {job_id: {status, progress, errors, metadata}}
_batch_jobs: dict[str, dict] = {}


def _initialize_job(
    job_id: str,
    user_id: uuid.UUID,
    email_ids: list[uuid.UUID],
    job_type: str,
) -> None:
    """Initialize batch job state in memory."""
    now = datetime.now(UTC).isoformat()
    _batch_jobs[job_id] = {
        "status": "queued",
        "progress": {
            "total": len(email_ids),
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
        },
        "errors": [],
        "metadata": {
            "user_id": str(user_id),
            "email_ids": [str(eid) for eid in email_ids],
            "job_type": job_type,
            "created_at": now,
            "updated_at": now,
        },
    }


def _update_job_status(job_id: str, new_status: str) -> None:
    """Update batch job status in memory."""
    job = _batch_jobs.get(job_id)
    if job is None:
        return
    now = datetime.now(UTC).isoformat()
    job["status"] = new_status
    job["metadata"]["updated_at"] = now
    if new_status in ("completed", "failed"):
        job["metadata"]["completed_at"] = now


def _update_progress(
    job_id: str,
    processed: int,
    succeeded: int,
    failed: int,
) -> None:
    """Update batch job progress in memory."""
    job = _batch_jobs.get(job_id)
    if job is None:
        return
    job["progress"]["processed"] = processed
    job["progress"]["succeeded"] = succeeded
    job["progress"]["failed"] = failed
    job["metadata"]["updated_at"] = datetime.now(UTC).isoformat()


def _add_error(job_id: str, email_id: uuid.UUID, error_message: str) -> None:
    """Add an error entry to the batch job."""
    job = _batch_jobs.get(job_id)
    if job is None:
        return
    job["errors"].append({
        "email_id": str(email_id),
        "error": error_message,
        "timestamp": datetime.now(UTC).isoformat(),
    })


async def batch_classify(
    db: AsyncSession,
    user_id: uuid.UUID,
    email_ids: list[uuid.UUID],
    background_tasks: BackgroundTasks,
) -> BatchJobResponse:
    """Queue a batch classification job and return immediately.

    Args:
        db: Database session
        user_id: ID of the user requesting the batch operation
        email_ids: List of email IDs to classify
        background_tasks: FastAPI BackgroundTasks for queuing

    Returns:
        BatchJobResponse with job_id for tracking
    """
    if not email_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email IDs provided.",
        )

    if len(email_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 emails allowed per batch.",
        )

    # Verify ownership of all emails
    result = await db.execute(
        select(Email).where(
            Email.id.in_(email_ids),
            Email.user_id == user_id,
        )
    )
    owned_emails = result.scalars().all()
    owned_ids = {e.id for e in owned_emails}

    invalid_ids = set(email_ids) - owned_ids
    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emails not found or not owned: {invalid_ids}",
        )

    # Generate job ID
    job_id = f"cls_{uuid.uuid4().hex[:16]}"

    # Initialize job in memory
    _initialize_job(job_id, user_id, email_ids, "classify")

    # Queue background task with tracking for graceful shutdown
    async_task = asyncio.create_task(
        _background_classify(job_id, user_id, email_ids)
    )
    async_task.set_name(f"batch_classify_{job_id}")
    get_task_tracker().add_task(async_task)

    logger.info(
        "Batch classify job queued: job_id=%s user_id=%s count=%d",
        job_id,
        user_id,
        len(email_ids),
    )

    return BatchJobResponse(
        job_id=job_id,
        status="queued",
        total=len(email_ids),
        processed=0,
        message="Batch classification job accepted and queued for processing",
    )


async def batch_process(
    db: AsyncSession,
    user: User,
    email_ids: list[uuid.UUID],
    background_tasks: BackgroundTasks,
) -> BatchJobResponse:
    """Queue a batch processing job and return immediately.

    Args:
        db: Database session
        user: User requesting the batch operation
        email_ids: List of email IDs to process
        background_tasks: FastAPI BackgroundTasks for queuing

    Returns:
        BatchJobResponse with job_id for tracking
    """
    if not email_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No email IDs provided.",
        )

    if len(email_ids) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 emails allowed per batch process.",
        )

    user_id = user.id

    # Verify ownership and status of all emails
    result = await db.execute(
        select(Email).where(
            Email.id.in_(email_ids),
            Email.user_id == user_id,
        )
    )
    owned_emails = result.scalars().all()
    owned_ids = {e.id for e in owned_emails}

    invalid_ids = set(email_ids) - owned_ids
    if invalid_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Emails not found or not owned: {invalid_ids}",
        )

    # Check for emails already being processed or sent
    invalid_status_emails = [
        e for e in owned_emails
        if e.status in {EmailStatus.PROCESSING, EmailStatus.SENT}
    ]
    if invalid_status_emails:
        invalid_email_ids = [str(e.id) for e in invalid_status_emails]
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Emails already processing or sent: {invalid_email_ids}",
        )

    # Generate job ID
    job_id = f"prc_{uuid.uuid4().hex[:16]}"

    # Initialize job in memory
    _initialize_job(job_id, user_id, email_ids, "process")

    # Queue background task with tracking for graceful shutdown
    async_task = asyncio.create_task(
        _background_process(job_id, user_id, email_ids)
    )
    async_task.set_name(f"batch_process_{job_id}")
    get_task_tracker().add_task(async_task)

    logger.info(
        "Batch process job queued: job_id=%s user_id=%s count=%d",
        job_id,
        user_id,
        len(email_ids),
    )

    return BatchJobResponse(
        job_id=job_id,
        status="queued",
        total=len(email_ids),
        processed=0,
        message="Batch processing job accepted and queued for processing",
    )


async def get_batch_status(
    job_id: str,
) -> BatchStatusResponse:
    """Get the current status of a batch job.

    Args:
        job_id: The batch job ID

    Returns:
        BatchStatusResponse with current job state

    Raises:
        HTTPException: 404 if job not found
    """
    job = _batch_jobs.get(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job {job_id} not found or expired.",
        )

    job_status = job["status"]
    progress = job["progress"]
    errors = job["errors"]
    metadata = job["metadata"]

    # Parse timestamps
    created_at = datetime.fromisoformat(metadata.get("created_at", datetime.now(UTC).isoformat()))
    updated_at_str = metadata.get("updated_at")
    completed_at_str = metadata.get("completed_at")

    updated_at = datetime.fromisoformat(updated_at_str) if updated_at_str else None
    completed_at = datetime.fromisoformat(completed_at_str) if completed_at_str else None

    return BatchStatusResponse(
        job_id=job_id,
        status=job_status,
        total=progress.get("total", 0),
        processed=progress.get("processed", 0),
        succeeded=progress.get("succeeded", 0),
        failed=progress.get("failed", 0),
        errors=errors if errors else None,
        created_at=created_at,
        updated_at=updated_at,
        completed_at=completed_at,
    )


async def _background_classify(
    job_id: str,
    user_id: uuid.UUID,
    email_ids: list[uuid.UUID],
) -> None:
    """Background task for batch email classification.

    Args:
        job_id: The batch job ID
        user_id: ID of the user who owns the emails
        email_ids: List of email IDs to classify
    """
    _update_job_status(job_id, "processing")

    gemini = get_gemini_client()
    processed = 0
    succeeded = 0
    failed = 0

    async with async_session_factory() as db:
        for email_id in email_ids:
            try:
                # Fetch email
                result = await db.execute(
                    select(Email).where(
                        Email.id == email_id,
                        Email.user_id == user_id,
                    )
                )
                email = result.scalar_one_or_none()

                if email is None:
                    _add_error(job_id, email_id, "Email not found")
                    failed += 1
                    processed += 1
                    _update_progress(job_id, processed, succeeded, failed)
                    continue

                # Skip already classified emails
                if email.classification is not None:
                    succeeded += 1
                    processed += 1
                    _update_progress(job_id, processed, succeeded, failed)
                    continue

                # Classify using Gemini
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
                    await db.flush()

                    succeeded += 1
                    logger.debug(
                        "Classified email %s as %s (%.2f confidence)",
                        email_id,
                        email.classification.value,
                        email.confidence,
                    )

                except Exception as exc:
                    error_msg = f"Classification failed: {exc}"
                    _add_error(job_id, email_id, error_msg)
                    failed += 1
                    logger.warning("Classification failed for email %s: %s", email_id, exc)

            except Exception as exc:
                error_msg = f"Unexpected error: {exc}"
                _add_error(job_id, email_id, error_msg)
                failed += 1
                logger.exception("Error processing email %s in batch classify", email_id)

            processed += 1
            _update_progress(job_id, processed, succeeded, failed)

        try:
            await db.commit()
        except Exception as exc:
            logger.error("Failed to commit batch classify results: %s", exc)
            await db.rollback()

    # Mark job as completed or failed
    final_status = "completed" if failed == 0 else "failed" if succeeded == 0 else "completed"
    _update_job_status(job_id, final_status)

    logger.info(
        "Batch classify job completed: job_id=%s processed=%d succeeded=%d failed=%d",
        job_id,
        processed,
        succeeded,
        failed,
    )


async def _background_process(
    job_id: str,
    user_id: uuid.UUID,
    email_ids: list[uuid.UUID],
) -> None:
    """Background task for batch email processing through agent pipeline.

    Args:
        job_id: The batch job ID
        user_id: ID of the user who owns the emails
        email_ids: List of email IDs to process
    """
    from app.agent.graph import process_email as agent_process_email

    _update_job_status(job_id, "processing")

    processed = 0
    succeeded = 0
    failed = 0

    async with async_session_factory() as db:
        for email_id in email_ids:
            try:
                # Fetch email and verify status
                result = await db.execute(
                    select(Email).where(
                        Email.id == email_id,
                        Email.user_id == user_id,
                    )
                )
                email = result.scalar_one_or_none()

                if email is None:
                    _add_error(job_id, email_id, "Email not found")
                    failed += 1
                    processed += 1
                    _update_progress(job_id, processed, succeeded, failed)
                    continue

                # Skip if already processing or sent
                if email.status in {EmailStatus.PROCESSING, EmailStatus.SENT}:
                    _add_error(
                        job_id,
                        email_id,
                        f"Email already in '{email.status.value}' state",
                    )
                    failed += 1
                    processed += 1
                    _update_progress(job_id, processed, succeeded, failed)
                    continue

                # Set to processing
                email.status = EmailStatus.PROCESSING
                await db.flush()

                # Run agent pipeline
                try:
                    await agent_process_email(email_id=email_id, db_session=db)
                    succeeded += 1
                    logger.debug("Processed email %s through agent pipeline", email_id)

                except Exception as exc:
                    error_msg = f"Agent pipeline failed: {exc}"
                    _add_error(job_id, email_id, error_msg)
                    failed += 1

                    # Try to recover status
                    try:
                        result = await db.execute(
                            select(Email).where(Email.id == email_id)
                        )
                        stuck_email = result.scalars().first()
                        if stuck_email and stuck_email.status == EmailStatus.PROCESSING:
                            stuck_email.status = EmailStatus.NEEDS_REVIEW
                            await db.flush()
                    except Exception as recovery_exc:
                        logger.error("Recovery failed for email %s: %s", email_id, recovery_exc)

                    logger.warning("Agent pipeline failed for email %s: %s", email_id, exc)

            except Exception as exc:
                error_msg = f"Unexpected error: {exc}"
                _add_error(job_id, email_id, error_msg)
                failed += 1
                logger.exception("Error processing email %s in batch process", email_id)

            processed += 1
            _update_progress(job_id, processed, succeeded, failed)

        try:
            await db.commit()
        except Exception as exc:
            logger.error("Failed to commit batch process results: %s", exc)
            await db.rollback()

    # Mark job as completed or failed
    if failed == 0:
        final_status = "completed"
    elif succeeded == 0:
        final_status = "failed"
    else:
        final_status = "completed"  # Partial success still marks as completed

    _update_job_status(job_id, final_status)

    logger.info(
        "Batch process job completed: job_id=%s processed=%d succeeded=%d failed=%d",
        job_id,
        processed,
        succeeded,
        failed,
    )
