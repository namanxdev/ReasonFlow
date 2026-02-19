"""Email template request/response schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TemplateResponse(BaseModel):
    """Template data response."""

    id: UUID
    user_id: UUID
    name: str
    subject_template: str
    body_template: str
    category: str | None
    variables: list
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TemplateCreateRequest(BaseModel):
    """Request to create a new email template."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., max_length=200)
    subject_template: str = Field(..., max_length=998)
    body_template: str
    category: str | None = Field(None, max_length=50)
    variables: list = Field(default_factory=list)
    is_active: bool = True


class TemplateUpdateRequest(BaseModel):
    """Request to update an existing email template."""

    name: str | None = Field(None, max_length=200)
    subject_template: str | None = Field(None, max_length=998)
    body_template: str | None = None
    category: str | None = Field(None, max_length=50)
    variables: list | None = None
    is_active: bool | None = None

    model_config = ConfigDict(extra="forbid")


class TemplateRenderRequest(BaseModel):
    """Request to render a template with variables."""

    model_config = ConfigDict(extra="forbid")

    variables: dict  # {"customer_name": "John", "order_id": "12345"}


class TemplateRenderResponse(BaseModel):
    """Rendered template output."""

    subject: str
    body: str
