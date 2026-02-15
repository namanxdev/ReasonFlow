"""Calendar request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AvailabilityRequest(BaseModel):
    """Query parameters for GET /calendar/availability."""

    model_config = ConfigDict(extra="forbid")

    start: datetime = Field(description="Start of the time range to check")
    end: datetime = Field(description="End of the time range to check")

    @model_validator(mode="after")
    def end_must_be_after_start(self) -> "AvailabilityRequest":
        if self.end <= self.start:
            raise ValueError("'end' must be strictly after 'start'")
        return self


class TimeSlot(BaseModel):
    """A single free time slot returned by the availability check."""

    model_config = ConfigDict(extra="forbid")

    start: datetime = Field(description="Slot start time")
    end: datetime = Field(description="Slot end time")
    duration_minutes: int = Field(ge=1, description="Slot length in minutes")


class AvailabilityResponse(BaseModel):
    """Response for GET /calendar/availability."""

    model_config = ConfigDict(extra="forbid")

    free_slots: list[TimeSlot] = Field(
        description="List of free time windows within the requested range"
    )
    checked_range_start: datetime = Field(description="Start of the range that was checked")
    checked_range_end: datetime = Field(description="End of the range that was checked")


class CreateEventRequest(BaseModel):
    """Request body for POST /calendar/events."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=500, description="Event title / summary")
    start: datetime = Field(description="Event start time")
    end: datetime = Field(description="Event end time")
    attendees: list[str] = Field(
        default_factory=list,
        description="List of attendee email addresses",
    )
    description: str | None = Field(
        default=None, max_length=8192, description="Optional event description"
    )
    location: str | None = Field(
        default=None, max_length=1024, description="Optional physical or virtual location"
    )

    @model_validator(mode="after")
    def end_must_be_after_start(self) -> "CreateEventRequest":
        if self.end <= self.start:
            raise ValueError("'end' must be strictly after 'start'")
        return self


class EventResponse(BaseModel):
    """Response for POST /calendar/events — the created calendar event."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Google Calendar event identifier")
    title: str = Field(description="Event title / summary")
    start: datetime = Field(description="Event start time")
    end: datetime = Field(description="Event end time")
    attendees: list[str] = Field(
        default_factory=list, description="Attendee email addresses"
    )
    description: str | None = Field(default=None, description="Event description")
    location: str | None = Field(default=None, description="Event location")
    html_link: str | None = Field(
        default=None, description="Google Calendar URL for this event"
    )
