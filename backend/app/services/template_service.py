"""Email template business logic."""

from __future__ import annotations

import logging
import re
import uuid
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_template import EmailTemplate
from app.schemas.template import TemplateCreateRequest, TemplateUpdateRequest

logger = logging.getLogger(__name__)

# Regex pattern for {{variable}} syntax
VARIABLE_PATTERN = re.compile(r"\{\{(\w+)\}\}")


async def list_templates(
    db: AsyncSession,
    user_id: uuid.UUID,
    category: str | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[EmailTemplate]:
    """Return a list of email templates for a user.

    Args:
        db: Database session
        user_id: User ID to filter templates
        category: Optional category filter
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return

    Returns:
        List of EmailTemplate objects
    """
    query = select(EmailTemplate).where(
        EmailTemplate.user_id == user_id,
        EmailTemplate.is_active.is_(True),
    )

    if category:
        query = query.where(EmailTemplate.category == category)

    query = query.order_by(EmailTemplate.name).offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_template(
    db: AsyncSession, user_id: uuid.UUID, template_id: uuid.UUID
) -> EmailTemplate:
    """Return a single template by ID, verifying ownership.

    Args:
        db: Database session
        user_id: User ID to verify ownership
        template_id: Template ID to retrieve

    Returns:
        EmailTemplate object

    Raises:
        HTTPException: 404 if template not found or doesn't belong to user
    """
    result = await db.execute(
        select(EmailTemplate).where(
            EmailTemplate.id == template_id,
            EmailTemplate.user_id == user_id,
        )
    )
    template: EmailTemplate | None = result.scalars().first()
    if template is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found.",
        )
    return template


async def create_template(
    db: AsyncSession, user_id: uuid.UUID, data: TemplateCreateRequest
) -> EmailTemplate:
    """Create a new email template.

    Args:
        db: Database session
        user_id: User ID for template ownership
        data: Template creation data

    Returns:
        Created EmailTemplate object
    """
    # Auto-extract variables from templates if not provided
    variables = data.variables if data.variables else []
    if not variables:
        subject_vars = set(VARIABLE_PATTERN.findall(data.subject_template))
        body_vars = set(VARIABLE_PATTERN.findall(data.body_template))
        variables = sorted(list(subject_vars | body_vars))

    template = EmailTemplate(
        user_id=user_id,
        name=data.name,
        subject_template=data.subject_template,
        body_template=data.body_template,
        category=data.category,
        variables=variables,
        is_active=data.is_active,
    )
    db.add(template)
    await db.flush()
    await db.refresh(template)

    logger.info("Created template id=%s for user=%s", template.id, user_id)
    return template


async def update_template(
    db: AsyncSession,
    user_id: uuid.UUID,
    template_id: uuid.UUID,
    data: TemplateUpdateRequest,
) -> EmailTemplate:
    """Update an existing email template.

    Args:
        db: Database session
        user_id: User ID to verify ownership
        template_id: Template ID to update
        data: Template update data

    Returns:
        Updated EmailTemplate object

    Raises:
        HTTPException: 404 if template not found or doesn't belong to user
    """
    template = await get_template(db, user_id, template_id)

    update_data: dict[str, Any] = data.model_dump(exclude_unset=True)

    # Update fields
    for field, value in update_data.items():
        if field == "variables" and value is None:
            continue
        setattr(template, field, value)

    # Re-extract variables if templates changed
    if "subject_template" in update_data or "body_template" in update_data:
        subject_vars = set(VARIABLE_PATTERN.findall(template.subject_template))
        body_vars = set(VARIABLE_PATTERN.findall(template.body_template))
        template.variables = sorted(list(subject_vars | body_vars))

    await db.flush()
    await db.refresh(template)

    logger.info("Updated template id=%s for user=%s", template.id, user_id)
    return template


async def delete_template(
    db: AsyncSession, user_id: uuid.UUID, template_id: uuid.UUID
) -> None:
    """Delete (soft-delete by deactivating) an email template.

    Args:
        db: Database session
        user_id: User ID to verify ownership
        template_id: Template ID to delete

    Raises:
        HTTPException: 404 if template not found or doesn't belong to user
    """
    template = await get_template(db, user_id, template_id)
    template.is_active = False
    await db.flush()

    logger.info("Deactivated template id=%s for user=%s", template_id, user_id)


async def render_template(
    template: EmailTemplate, variables: dict[str, Any]
) -> tuple[str, str]:
    """Render a template with variable substitution.

    Uses {{variable}} syntax for variable placeholders.

    Args:
        template: EmailTemplate to render
        variables: Dictionary of variable names to values

    Returns:
        Tuple of (rendered_subject, rendered_body)

    Raises:
        HTTPException: 400 if required variables are missing
    """
    subject = template.subject_template
    body = template.body_template

    # Find all variables used in templates
    required_vars = set(VARIABLE_PATTERN.findall(subject))
    required_vars.update(VARIABLE_PATTERN.findall(body))

    # Check for missing variables
    missing_vars = required_vars - set(variables.keys())
    if missing_vars:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required variables: {sorted(missing_vars)}",
        )

    # Replace variables in subject
    def replace_var(match: re.Match) -> str:
        var_name = match.group(1)
        return str(variables.get(var_name, match.group(0)))

    rendered_subject = VARIABLE_PATTERN.sub(replace_var, subject)
    rendered_body = VARIABLE_PATTERN.sub(replace_var, body)

    logger.debug(
        "Rendered template id=%s with variables=%s",
        template.id,
        list(variables.keys()),
    )
    return rendered_subject, rendered_body
