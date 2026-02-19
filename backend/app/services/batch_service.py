"""Batch operation business logic with background task processing."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime

import redis.asyncio as redis
from fastapi import BackgroundTasks, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session_factory
from app.core.redis import get_redis_client
from app.llm.client import get_gemini_client
from app.models.email import Email, EmailClassification, EmailStatus
from app.models.user import User
from app.schemas.batch import BatchJobResponse, BatchStatusResponse

logger = logging.getLogger(__name__)

# Redis key prefixes and TTL
BATCH_KEY_PREFIX = "batch"
BATCH_TTL_SECONDS = 86400  # 24 hours


def _get_redis_keys(job_id: str) -> dict[str, str]:
    """Generate Redis key names for a batch job."""
    return {
        "status": f"{BATCH_KEY_PREFIX}:{job_id}:status",
        "progress": f"{BATCH_KEY_PREFIX}:{job_id}:progress",
        "errors": f"{BATCH_KEY_PREFIX}:{job_id}:errors",
        "metadata": f"{BATCH_KEY_PREFIX}:{job_id}:metadata",
    }


async def _initialize_job(
    redis_client: redis.Redis,
    job_id: str,
    user_id: uuid.UUID,
    email_ids: list[uuid.UUID],
    job_type: str,
) -> None:
    """Initialize batch job state in Redis."""
    keys = _get_redis_keys(job_id)
    now = datetime.now(UTC).isoformat()

    pipe = redis_client.pipeline()

    # Set initial status
    pipe.setex(
        keys["status"],
        BATCH_TTL_SECONDS,
        "queued",
    )

    # Set progress info
    pipe.setex(
        keys["progress"],
        BATCH_TTL_SECONDS,
        json.dumps({
            "total": len(email_ids),
            "processed": 0,
            "succeeded": 0,
            "failed": 0,
        }),
    )

    # Initialize empty errors list
    pipe.setex(
        keys["errors"],
        BATCH_TTL_SECONDS,
        json.dumps([]),
    )

    # Set metadata
    pipe.setex(
        keys["metadata"],
        BATCH_TTL_SECONDS,
        json.dumps({
            "user_id": str(user_id),
            "email_ids": [str(eid) for eid in email_ids],
            "job_type": job_type,
            "created_at": now,
            "updated_at": now,
        }),
    )

    await pipe.execute()


async def _update_job_status(
    redis_client: redis.Redis,
    job_id: str,
    status: str,
) -> None:
    """Update batch job status in Redis."""
    keys = _get_redis_keys(job_id)
    now = datetime.now(UTC).isoformat()

    pipe = redis_client.pipeline()
    pipe.setex(keys["status"], BATCH_TTL_SECONDS, status)

    # Update metadata with new timestamp
    metadata_raw = await redis_client.get(keys["metadata"])
    if metadata_raw:
        metadata = json.loads(metadata_raw)
        metadata["updated_at"] = now
        if status in ("completed", "failed"):
            metadata["completed_at"] = now
        pipe.setex(keys["metadata"], BATCH_TTL_SECONDS, json.dumps(metadata))

    await pipe.execute()


async def _update_progress(
    redis_client: redis.Redis,
    job_id: str,
    processed: int,
    succeeded: int,
    failed: int,
) -> None:
    """Update batch job progress in Redis."""
    keys = _get_redis_keys(job_id)
    now = datetime.now(UTC).isoformat()

    pipe = redis_client.pipeline()

    # Update progress
    progress_raw = await redis_client.get(keys["progress"])
    if progress_raw:
        progress = json.loads(progress_raw)
        progress["processed"] = processed
        progress["succeeded"] = succeeded
        progress["failed"] = failed
        pipe.setex(keys["progress"], BATCH_TTL_SECONDS, json.dumps(progress))

    # Update metadata timestamp
    metadata_raw = await redis_client.get(keys["metadata"])
    if metadata_raw:
        metadata = json.loads(metadata_raw)
        metadata["updated_at"] = now
        pipe.setex(keys["metadata"], BATCH_TTL_SECONDS, json.dumps(metadata))

    await pipe.execute()


async def _add_error(
    redis_client: redis.Redis,
    job_id: str,
    email_id: uuid.UUID,
    error_message: str,
) -> None:
    """Add an error entry to the batch job."""
    keys = _get_redis_keys(job_id)

    errors_raw = await redis_client.get(keys["errors"])
    errors = json.loads(errors_raw) if errors_raw else []

    errors.append({
        "email_id": str(email_id),
        "error": error_message,
        "timestamp": datetime.now(UTC).isoformat(),
    })

    await redis_client.setex(
        keys["errors"],
        BATCH_TTL_SECONDS,
        json.dumps(errors),
    )


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

    # Initialize job in Redis
    redis_client = await get_redis_client()
    await _initialize_job(redis_client, job_id, user_id, email_ids, "classify")

    # Queue background task
    background_tasks.add_task(
        _background_classify,
        job_id,
        user_id,
        email_ids,
    )

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

    # Initialize job in Redis
    redis_client = await get_redis_client()
    await _initialize_job(redis_client, job_id, user_id, email_ids, "process")

    # Queue background task
    background_tasks.add_task(
        _background_process,
        job_id,
        user_id,
        email_ids,
    )

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
    redis_client: redis.Redis,
) -> BatchStatusResponse:
    """Get the current status of a batch job.

    Args:
        job_id: The batch job ID
        redis_client: Redis client

    Returns:
        BatchStatusResponse with current job state

    Raises:
        HTTPException: 404 if job not found
    """
    keys = _get_redis_keys(job_id)

    # Fetch all data from Redis
    status_raw = await redis_client.get(keys["status"])
    if status_raw is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Batch job {job_id} not found or expired.",
        )

    progress_raw = await redis_client.get(keys["progress"])
    errors_raw = await redis_client.get(keys["errors"])
    metadata_raw = await redis_client.get(keys["metadata"])

    job_status = status_raw.decode() if isinstance(status_raw, bytes) else status_raw
    progress = json.loads(progress_raw) if progress_raw else {}
    errors = json.loads(errors_raw) if errors_raw else []
    metadata = json.loads(metadata_raw) if metadata_raw else {}

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
    redis_client = await get_redis_client()
    await _update_job_status(redis_client, job_id, "processing")

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
                    await _add_error(redis_client, job_id, email_id, "Email not found")
                    failed += 1
                    processed += 1
                    await _update_progress(redis_client, job_id, processed, succeeded, failed)
                    continue

                # Skip already classified emails
                if email.classification is not None:
                    succeeded += 1
                    processed += 1
                    await _update_progress(redis_client, job_id, processed, succeeded, failed)
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
                    await _add_error(redis_client, job_id, email_id, error_msg)
                    failed += 1
                    logger.warning("Classification failed for email %s: %s", email_id, exc)

            except Exception as exc:
                error_msg = f"Unexpected error: {exc}"
                await _add_error(redis_client, job_id, email_id, error_msg)
                failed += 1
                logger.exception("Error processing email %s in batch classify", email_id)

            processed += 1
            await _update_progress(redis_client, job_id, processed, succeeded, failed)

        try:
            await db.commit()
        except Exception as exc:
            logger.error("Failed to commit batch classify results: %s", exc)
            await db.rollback()

    # Mark job as completed or failed
    final_status = "completed" if failed == 0 else "failed" if succeeded == 0 else "completed"
    await _update_job_status(redis_client, job_id, final_status)

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

    redis_client = await get_redis_client()
    await _update_job_status(redis_client, job_id, "processing")

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
                    await _add_error(redis_client, job_id, email_id, "Email not found")
                    failed += 1
                    processed += 1
                    await _update_progress(redis_client, job_id, processed, succeeded, failed)
                    continue

                # Skip if already processing or sent
                if email.status in {EmailStatus.PROCESSING, EmailStatus.SENT}:
                    await _add_error(
                        redis_client,
                        job_id,
                        email_id,
                        f"Email already in '{email.status.value}' state",
                    )
                    failed += 1
                    processed += 1
                    await _update_progress(redis_client, job_id, processed, succeeded, failed)
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
                    await _add_error(redis_client, job_id, email_id, error_msg)
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
                await _add_error(redis_client, job_id, email_id, error_msg)
                failed += 1
                logger.exception("Error processing email %s in batch process", email_id)

            processed += 1
            await _update_progress(redis_client, job_id, processed, succeeded, failed)

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

    await _update_job_status(redis_client, job_id, final_status)

    logger.info(
        "Batch process job completed: job_id=%s processed=%d succeeded=%d failed=%d",
        job_id,
        processed,
        succeeded,
        failed,
    )
