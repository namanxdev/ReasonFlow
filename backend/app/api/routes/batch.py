"""Batch operation API routes for bulk email processing."""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.redis import get_redis
from app.models.user import User
from app.schemas.batch import (
    BatchClassifyRequest,
    BatchJobResponse,
    BatchProcessRequest,
    BatchStatusResponse,
)
from app.services import batch_service

router = APIRouter()


@router.post(
    "/classify",
    response_model=BatchJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Batch classify emails",
    description="""
    Queue multiple emails for background classification.

    Returns immediately with a job_id that can be used to poll for status.
    Maximum 100 emails per batch.
    """,
)
async def batch_classify_emails(
    request: BatchClassifyRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchJobResponse:
    """Submit a batch of emails for classification.

    The classification runs in the background. Use the returned job_id
    with the /status/{job_id} endpoint to track progress.
    """
    return await batch_service.batch_classify(
        db=db,
        user_id=current_user.id,
        email_ids=request.email_ids,
        background_tasks=background_tasks,
    )


@router.post(
    "/process",
    response_model=BatchJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Batch process emails through agent pipeline",
    description="""
    Queue multiple emails for background processing through the full
    agent pipeline (classify, retrieve, decide, generate, review).

    Returns immediately with a job_id that can be used to poll for status.
    Maximum 50 emails per batch.

    Emails must not be in 'processing' or 'sent' status.
    """,
)
async def batch_process_emails(
    request: BatchProcessRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BatchJobResponse:
    """Submit a batch of emails for full agent processing.

    The processing runs in the background. Use the returned job_id
    with the /status/{job_id} endpoint to track progress.
    """
    return await batch_service.batch_process(
        db=db,
        user=current_user,
        email_ids=request.email_ids,
        background_tasks=background_tasks,
    )


@router.get(
    "/status/{job_id}",
    response_model=BatchStatusResponse,
    summary="Get batch job status",
    description="""
    Retrieve the current status of a batch job including:
    - Current status (queued, processing, completed, failed)
    - Progress counters (total, processed, succeeded, failed)
    - Error details for failed emails
    - Timestamps for created, updated, and completed

    Job data is retained for 24 hours after completion.
    """,
)
async def get_batch_job_status(
    job_id: str,
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user),
) -> BatchStatusResponse:
    """Get the current status of a batch job.

    Poll this endpoint to track progress of batch operations.
    Recommended polling interval: 2-3 seconds.
    """
    return await batch_service.get_batch_status(job_id, redis_client=redis)
