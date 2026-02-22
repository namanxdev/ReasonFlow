"""Email request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.models.email import EmailClassification, EmailStatus
from app.schemas.common import PaginatedResponse


class EmailResponse(BaseModel):
    """Single email record as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Email record identifier")
    gmail_id: str = Field(description="Gmail message identifier")
    subject: str = Field(description="Email subject line")
    sender: EmailStr = Field(description="Sender email address")
    received_at: datetime = Field(description="Timestamp when the email was received")
    classification: EmailClassification | None = Field(
        default=None, description="Agent-assigned classification"
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Classification confidence score (0–1)",
    )
    status: EmailStatus = Field(description="Current processing pipeline status")


class EmailDetailResponse(EmailResponse):
    """Email record with full body and draft — used by GET /emails/{id}."""

    body: str = Field(description="Full email body content")
    thread_id: str | None = Field(default=None, description="Gmail thread identifier")
    recipient: str | None = Field(default=None, description="Recipient email address")
    draft_response: str | None = Field(
        default=None, description="AI-generated draft reply, if any"
    )


# Convenience type alias matching the paginated list structure from the API docs.
EmailListResponse = PaginatedResponse[EmailResponse]


class EmailFilterParams(BaseModel):
    """Query parameters accepted by GET /emails."""

    model_config = ConfigDict(extra="forbid")

    status: EmailStatus | None = Field(
        default=None, description="Filter by processing status"
    )
    classification: EmailClassification | None = Field(
        default=None, description="Filter by classification"
    )
    search: str | None = Field(
        default=None,
        max_length=255,
        description="Full-text search against subject and sender",
    )
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: str | None = Field(default=None, description="Sort field")
    sort_order: str | None = Field(default="desc", description="Sort order: asc or desc")


class EmailCreate(BaseModel):
    """Schema for creating/saving emails."""

    model_config = ConfigDict(extra="forbid")

    subject: str = Field(max_length=998, description="Email subject line (RFC 2822 limit)")  # RFC 2822 limit
    body: str = Field(description="Full email body content")  # Validated below
    sender: str = Field(max_length=320, description="Sender email address (RFC 5321 limit)")  # RFC 5321 limit

    @field_validator("body")
    @classmethod
    def validate_body_size(cls, v: str) -> str:
        """Validate email body does not exceed maximum size to prevent LLM token overflow."""
        max_body_size = 50000  # ~50KB limit
        if len(v) > max_body_size:
            raise ValueError(f"Email body exceeds maximum size of {max_body_size} characters")
        return v


class EmailProcessRequest(BaseModel):
    """Request body for POST /emails/{id}/process.

    Currently no body fields are required — the email ID comes from the
    path parameter — but this schema is kept for forward-compatibility.
    """

    model_config = ConfigDict(extra="forbid")


class EmailProcessResponse(BaseModel):
    """Response body for POST /emails/{id}/process (202 Accepted)."""

    model_config = ConfigDict(extra="forbid")

    trace_id: uuid.UUID = Field(description="Identifier for the new agent trace")
    status: str = Field(default="processing", description="Initial processing status")


class EmailStatsResponse(BaseModel):
    """Response body for GET /emails/stats — email counts by status."""

    model_config = ConfigDict(extra="forbid")

    pending: int = Field(default=0, description="Count of pending emails")
    processing: int = Field(default=0, description="Count of processing emails")
    drafted: int = Field(default=0, description="Count of drafted emails")
    needs_review: int = Field(default=0, description="Count of emails needing review")
    approved: int = Field(default=0, description="Count of approved emails")
    sent: int = Field(default=0, description="Count of sent emails")
    rejected: int = Field(default=0, description="Count of rejected emails")
    total: int = Field(default=0, description="Total count of all emails")
