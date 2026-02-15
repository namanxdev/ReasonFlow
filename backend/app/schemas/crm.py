"""CRM contact request/response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ContactResponse(BaseModel):
    """CRM contact record as returned by GET /crm/contacts/{email}."""

    model_config = ConfigDict(extra="ignore")

    email: EmailStr = Field(description="Contact email address (primary key in the API)")
    name: str | None = Field(default=None, description="Full name")
    company: str | None = Field(default=None, description="Company or organisation name")
    title: str | None = Field(default=None, description="Job title")
    phone: str | None = Field(default=None, description="Phone number")
    notes: str | None = Field(default=None, description="Free-text notes about the contact")
    tags: list[str] = Field(
        default_factory=list, description="Labels / tags associated with this contact"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary extra fields stored for this contact"
    )
    last_contacted_at: datetime | None = Field(
        default=None, description="Timestamp of the most recent interaction"
    )
    created_at: datetime | None = Field(
        default=None, description="When this contact record was created"
    )
    updated_at: datetime | None = Field(
        default=None, description="When this contact record was last updated"
    )


class ContactUpdateRequest(BaseModel):
    """Request body for PUT /crm/contacts/{email} — partial update."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, description="Full name")
    company: str | None = Field(default=None, description="Company or organisation name")
    title: str | None = Field(default=None, description="Job title")
    phone: str | None = Field(default=None, description="Phone number")
    notes: str | None = Field(default=None, description="Free-text notes")
    tags: list[str] | None = Field(
        default=None, description="Replacement tag list (replaces existing tags if provided)"
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Arbitrary extra fields (merged with existing metadata if provided)",
    )
