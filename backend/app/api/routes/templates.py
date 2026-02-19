"""Email template API routes."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.template import (
    TemplateCreateRequest,
    TemplateRenderRequest,
    TemplateRenderResponse,
    TemplateResponse,
    TemplateUpdateRequest,
)
from app.services import template_service

router = APIRouter()


@router.get(
    "",
    response_model=list[TemplateResponse],
    summary="List email templates",
)
async def list_templates(
    category: str | None = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[TemplateResponse]:
    """Return a list of email templates for the current user."""
    templates = await template_service.list_templates(
        db, user.id, category=category, skip=skip, limit=limit
    )
    return [TemplateResponse.model_validate(t) for t in templates]


@router.post(
    "",
    response_model=TemplateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new email template",
)
async def create_template(
    data: TemplateCreateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TemplateResponse:
    """Create a new email template."""
    template = await template_service.create_template(db, user.id, data)
    return TemplateResponse.model_validate(template)


@router.get(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Get a single email template",
)
async def get_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TemplateResponse:
    """Return a single email template by ID."""
    template = await template_service.get_template(db, user.id, template_id)
    return TemplateResponse.model_validate(template)


@router.put(
    "/{template_id}",
    response_model=TemplateResponse,
    summary="Update an email template",
)
async def update_template(
    template_id: uuid.UUID,
    data: TemplateUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TemplateResponse:
    """Update an existing email template."""
    template = await template_service.update_template(db, user.id, template_id, data)
    return TemplateResponse.model_validate(template)


@router.delete(
    "/{template_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an email template",
)
async def delete_template(
    template_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Delete (deactivate) an email template."""
    await template_service.delete_template(db, user.id, template_id)


@router.post(
    "/{template_id}/render",
    response_model=TemplateRenderResponse,
    summary="Render a template with variables",
)
async def render_template(
    template_id: uuid.UUID,
    data: TemplateRenderRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TemplateRenderResponse:
    """Render a template with the provided variables.

    Use {{variable_name}} syntax in templates. Provide variable values
    in the request body to substitute them.
    """
    template = await template_service.get_template(db, user.id, template_id)
    subject, body = await template_service.render_template(template, data.variables)
    return TemplateRenderResponse(subject=subject, body=body)
