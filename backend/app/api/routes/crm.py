"""CRM contact API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import EmailStr

from app.core.deps import get_current_user
from app.integrations.crm.factory import get_crm_client
from app.models.user import User
from app.schemas.crm import ContactResponse, ContactUpdateRequest

router = APIRouter()


@router.get(
    "/contacts",
    response_model=list[ContactResponse],
    summary="List all contacts or search",
)
async def list_contacts(
    q: str | None = Query(None, description="Search query"),
    _user: User = Depends(get_current_user),
) -> list[ContactResponse]:
    """List all CRM contacts, optionally filtered by a search query."""
    client = get_crm_client()
    if q:
        results = await client.search_contacts(q)
    else:
        results = await client.search_contacts("")  # returns all
    return [ContactResponse(**c) for c in results]


@router.get(
    "/contacts/{email}",
    response_model=ContactResponse,
    summary="Get contact information by email",
)
async def get_contact(
    email: EmailStr = Path(..., description="Contact email address"),
    _user: User = Depends(get_current_user),
) -> ContactResponse:
    """Look up a CRM contact record by email address."""
    client = get_crm_client()
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
    _user: User = Depends(get_current_user),
) -> ContactResponse:
    """Create or update a CRM contact record."""
    client = get_crm_client()
    data = body.model_dump(exclude_unset=True)
    updated = await client.update_contact(email, data)
    return ContactResponse(**updated)
