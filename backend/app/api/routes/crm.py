"""CRM contact API routes."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.integrations.crm.factory import get_crm_client
from app.integrations.crm.db_crm import DatabaseCRM
from app.models.user import User
from app.schemas.crm import ContactResponse, ContactUpdateRequest


def sanitize_search_query(query: str | None) -> str | None:
    """Sanitize search query to prevent injection attacks (VAL-5 fix).
    
    Removes potentially dangerous characters and limits query length.
    
    Args:
        query: Raw search query string
        
    Returns:
        Sanitized query string or None
    """
    if not query:
        return None
    
    # Limit length
    query = query[:100]
    
    # Remove potentially dangerous characters (SQL injection, regex injection)
    # Allow alphanumeric, spaces, @, ., -, _, and common search operators
    sanitized = re.sub(r'[^\w\s@.\-_]', '', query)
    
    # Remove SQL keywords that could be used for injection
    sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION', 'WHERE', 'FROM']
    for keyword in sql_keywords:
        sanitized = re.sub(rf'\b{keyword}\b', '', sanitized, flags=re.IGNORECASE)
    
    # Collapse multiple spaces
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    
    return sanitized if sanitized else None

router = APIRouter()


class PaginatedContactsResponse(BaseModel):
    items: list[ContactResponse]
    total: int
    page: int
    per_page: int


class ContactEmailResponse(BaseModel):
    id: str
    subject: str | None = None
    sender: str | None = None
    recipient: str | None = None
    received_at: str | None = None
    classification: str | None = None
    status: str | None = None


@router.get(
    "/contacts",
    response_model=PaginatedContactsResponse,
    summary="List contacts with pagination",
)
async def list_contacts(
    q: str | None = Query(None, description="Search query"),
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PaginatedContactsResponse:
    """List CRM contacts with pagination and optional search."""
    # Sanitize search query (VAL-5 fix)
    q = sanitize_search_query(q)
    
    client = get_crm_client(db=db, user_id=user.id)
    if isinstance(client, DatabaseCRM):
        items, total = await client.list_contacts_paginated(page=page, per_page=per_page, query=q)
    else:
        results = await client.search_contacts(q or "")
        total = len(results)
        start = (page - 1) * per_page
        items = results[start : start + per_page]
    return PaginatedContactsResponse(
        items=[ContactResponse(**c) for c in items],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get(
    "/contacts/{email}",
    response_model=ContactResponse,
    summary="Get contact information by email",
)
async def get_contact(
    email: EmailStr = Path(..., description="Contact email address"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContactResponse:
    """Look up a CRM contact record by email address."""
    client = get_crm_client(db=db, user_id=user.id)
    contact = await client.get_contact(email)
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No contact found for email: {email}",
        )
    return ContactResponse(**contact)


@router.put(
    "/contacts/{email}",
    response_model=ContactResponse,
    summary="Update contact information",
)
async def update_contact(
    body: ContactUpdateRequest,
    email: EmailStr = Path(..., description="Contact email address"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ContactResponse:
    """Create or update a CRM contact record."""
    client = get_crm_client(db=db, user_id=user.id)
    data = body.model_dump(exclude_unset=True)
    updated = await client.update_contact(email, data)
    return ContactResponse(**updated)


@router.delete(
    "/contacts/{email}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a contact",
)
async def delete_contact(
    email: EmailStr = Path(..., description="Contact email address"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    """Delete a CRM contact by email."""
    from sqlalchemy import select, delete as sa_delete
    from app.models.contact import Contact

    result = await db.execute(
        select(Contact).where(
            Contact.user_id == user.id,
            Contact.email == email.lower(),
        )
    )
    contact = result.scalars().first()
    if contact is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No contact found for email: {email}",
        )
    await db.delete(contact)
    await db.flush()


@router.get(
    "/contacts/{email}/emails",
    response_model=list[ContactEmailResponse],
    summary="Get email history for a contact",
)
async def get_contact_emails(
    email: EmailStr = Path(..., description="Contact email address"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ContactEmailResponse]:
    """Fetch email history associated with a contact."""
    client = get_crm_client(db=db, user_id=user.id)
    if isinstance(client, DatabaseCRM):
        emails = await client.get_contact_emails(email, limit=limit)
        return [ContactEmailResponse(**e) for e in emails]
    return []
