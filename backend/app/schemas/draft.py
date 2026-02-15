"""Draft request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.email import EmailClassification, EmailStatus
from app.schemas.common import PaginatedResponse


class DraftResponse(BaseModel):
    """A single draft awaiting human review."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Draft (email) record identifier")
    subject: str = Field(description="Original email subject line")
    sender: str = Field(description="Original sender email address")
    received_at: datetime = Field(description="When the original email was received")
    classification: EmailClassification | None = Field(
        default=None, description="Agent-assigned email classification"
    )
    confidence: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Classification confidence score (0–1)",
    )
    status: EmailStatus = Field(description="Current pipeline status")
    draft_response: str | None = Field(
        default=None, description="AI-generated draft reply content"
    )
    created_at: datetime = Field(description="When the record was created")
    updated_at: datetime = Field(description="When the record was last updated")


# Convenience alias for the paginated draft list.
DraftListResponse = PaginatedResponse[DraftResponse]


class DraftEditRequest(BaseModel):
    """Request body for PUT /drafts/{id} — edit draft content before sending."""

    model_config = ConfigDict(extra="forbid")

    content: str = Field(
        min_length=1,
        description="Updated draft reply text",
    )
