"""Notification and WebSocket schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class NotificationEvent(BaseModel):
    """Notification event schema for WebSocket messages."""

    type: str = Field(..., description="Event type (EventType value)")
    user_id: UUID = Field(..., description="User ID this event is for")
    data: dict[str, Any] = Field(default_factory=dict, description="Event payload data")
    timestamp: datetime = Field(..., description="Event timestamp (UTC)")

    model_config = {"from_attributes": True}


class WebSocketAuthMessage(BaseModel):
    """WebSocket authentication message - must be sent as first message."""

    token: str = Field(..., description="JWT access token for authentication")


class WebSocketConnectedMessage(BaseModel):
    """WebSocket connected confirmation message."""

    type: str = Field(default="connected", description="Message type")
    user_id: str = Field(..., description="Authenticated user ID")


# Event payload schemas for type safety and documentation

class EmailReceivedPayload(BaseModel):
    """Payload for EMAIL_RECEIVED event."""

    email_id: str = Field(..., description="ID of the received email")
    subject: str = Field(..., description="Email subject")
    sender: str = Field(..., description="Email sender")


class EmailClassifiedPayload(BaseModel):
    """Payload for EMAIL_CLASSIFIED event."""

    email_id: str = Field(..., description="ID of the classified email")
    classification: str = Field(..., description="Email classification (intent)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Classification confidence")


class DraftReadyPayload(BaseModel):
    """Payload for DRAFT_READY event."""

    draft_id: str = Field(..., description="ID of the generated draft")
    email_id: str = Field(..., description="ID of the source email")
    requires_approval: bool = Field(..., description="Whether draft requires human approval")


class DraftApprovedPayload(BaseModel):
    """Payload for DRAFT_APPROVED event."""

    draft_id: str = Field(..., description="ID of the approved draft")
    email_id: str = Field(..., description="ID of the related email")


class DraftRejectedPayload(BaseModel):
    """Payload for DRAFT_REJECTED event."""

    draft_id: str = Field(..., description="ID of the rejected draft")
    email_id: str = Field(..., description="ID of the related email")
    reason: str | None = Field(default=None, description="Optional rejection reason")


class EmailSentPayload(BaseModel):
    """Payload for EMAIL_SENT event."""

    email_id: str = Field(..., description="ID of the sent email")
    draft_id: str | None = Field(default=None, description="ID of the sent draft (if applicable)")


class BatchProgressPayload(BaseModel):
    """Payload for BATCH_PROGRESS event."""

    job_id: str = Field(..., description="Batch job ID")
    processed: int = Field(..., ge=0, description="Number of items processed")
    total: int = Field(..., ge=0, description="Total number of items")
    percentage: int = Field(..., ge=0, le=100, description="Progress percentage")


class BatchCompletePayload(BaseModel):
    """Payload for BATCH_COMPLETE event."""

    job_id: str = Field(..., description="Batch job ID")
    status: str = Field(..., description="Batch status (completed, failed, partial)")
    succeeded: int = Field(..., ge=0, description="Number of successful items")
    failed: int = Field(..., ge=0, description="Number of failed items")
