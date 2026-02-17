"""Calendar API routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import decrypt_oauth_token
from app.integrations.calendar.client import CalendarClient
from app.models.user import User
from app.schemas.calendar import (
    AvailabilityResponse,
    CreateEventRequest,
    EventResponse,
    TimeSlot,
)

router = APIRouter()


def _build_calendar_client(user: User) -> CalendarClient:
    """Construct a CalendarClient from the user's encrypted OAuth credentials."""
    if not user.oauth_token_encrypted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gmail / Calendar account not connected. Complete the OAuth flow first.",
        )
    credentials: dict[str, str] = {
        "access_token": decrypt_oauth_token(user.oauth_token_encrypted),
    }
    if user.oauth_refresh_token_encrypted:
        credentials["refresh_token"] = decrypt_oauth_token(user.oauth_refresh_token_encrypted)
    return CalendarClient(credentials)


@router.get(
    "/availability",
    response_model=AvailabilityResponse,
    summary="Check free time slots",
)
async def check_availability(
    start: datetime = Query(..., description="Start of range"),
    end: datetime = Query(..., description="End of range"),
    user: User = Depends(get_current_user),
) -> AvailabilityResponse:
    """Return free time windows within the requested date range."""
    if end <= start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="'end' must be strictly after 'start'.",
        )
    client = _build_calendar_client(user)
    try:
        free_slots = await client.get_free_slots(start.date())
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Calendar API error: {exc}",
        ) from exc

    return AvailabilityResponse(
        free_slots=[TimeSlot(**slot) for slot in free_slots],
        checked_range_start=start,
        checked_range_end=end,
    )


@router.get(
    "/events",
    summary="List calendar events",
)
async def list_events(
    start: datetime = Query(..., description="Start of range"),
    end: datetime = Query(..., description="End of range"),
    user: User = Depends(get_current_user),
) -> list[dict]:
    """Return calendar events within the requested date range."""
    client = _build_calendar_client(user)
    try:
        events = await client.list_events(time_min=start, time_max=end)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Calendar API error: {exc}",
        ) from exc
    return [
        {
            "id": e.get("id", ""),
            "title": e.get("summary", "Untitled"),
            "start": e.get("start", {}).get("dateTime", e.get("start", {}).get("date", "")),
            "end": e.get("end", {}).get("dateTime", e.get("end", {}).get("date", "")),
            "attendees": [a.get("email", "") for a in e.get("attendees", [])],
            "html_link": e.get("htmlLink", ""),
        }
        for e in events
    ]


@router.post(
    "/events",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a calendar event",
)
async def create_event(
    body: CreateEventRequest,
    user: User = Depends(get_current_user),
) -> EventResponse:
    """Create a new Google Calendar event."""
    client = _build_calendar_client(user)
    try:
        data = await client.create_event(
            summary=body.title,
            start=body.start,
            end=body.end,
            attendees=body.attendees,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Calendar API error: {exc}",
        ) from exc

    return EventResponse(
        id=data.get("id", ""),
        title=data.get("summary", body.title),
        start=body.start,
        end=body.end,
        attendees=body.attendees,
        description=body.description,
        location=body.location,
        html_link=data.get("htmlLink"),
    )
