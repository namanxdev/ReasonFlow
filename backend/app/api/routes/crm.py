"""CRM contact API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import get_current_user
from app.integrations.crm.factory import get_crm_client
from app.models.user import User
from app.schemas.crm import ContactResponse, ContactUpdateRequest

router = APIRouter()


@router.get(
    "/contacts/{email}",
    response_model=ContactResponse,
    summary="Get contact information by email",
)
async def get_contact(
    email: str,
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
    email: str,
    body: ContactUpdateRequest,
    _user: User = Depends(get_current_user),
) -> ContactResponse:
    """Create or update a CRM contact record."""
    client = get_crm_client()
    data = body.model_dump(exclude_unset=True)
    updated = await client.update_contact(email, data)
    return ContactResponse(**updated)
