"""Batch operation request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BatchClassifyRequest(BaseModel):
    """Request body for batch email classification."""

    model_config = ConfigDict(extra="forbid")

    email_ids: list[uuid.UUID] = Field(
        ...,
        max_length=100,
        description="List of email IDs to classify (max 100)",
    )


class BatchProcessRequest(BaseModel):
    """Request body for batch email processing."""

    model_config = ConfigDict(extra="forbid")

    email_ids: list[uuid.UUID] = Field(
        ...,
        max_length=50,
        description="List of email IDs to process (max 50)",
    )


class BatchJobResponse(BaseModel):
    """Response body for batch job submission (202 Accepted)."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(description="Unique job identifier for tracking")
    status: str = Field(
        default="queued",
        description="Job status: queued, processing, completed, or failed",
    )
    total: int = Field(description="Total number of emails in the batch")
    processed: int = Field(
        default=0,
        description="Number of emails processed so far",
    )
    message: str = Field(
        default="Batch job accepted and queued for processing",
        description="Human-readable status message",
    )


class BatchStatusResponse(BaseModel):
    """Response body for batch job status query."""

    model_config = ConfigDict(extra="forbid")

    job_id: str = Field(description="Unique job identifier")
    status: str = Field(
        description="Job status: queued, processing, completed, or failed"
    )
    total: int = Field(description="Total number of emails in the batch")
    processed: int = Field(description="Number of emails processed")
    succeeded: int = Field(description="Number of emails successfully processed")
    failed: int = Field(description="Number of emails that failed processing")
    errors: list[dict] | None = Field(
        default=None,
        description="List of errors with email_id and error message",
    )
    created_at: datetime = Field(description="Timestamp when job was created")
    updated_at: datetime | None = Field(
        default=None,
        description="Timestamp of last status update",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when job completed",
    )
