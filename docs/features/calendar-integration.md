# Calendar Integration

## Overview

Google Calendar integration enables the agent to check availability, detect conflicts, and create events when processing meeting-related emails.

## CalendarClient API

```python
class CalendarClient:
    async def get_free_slots(start: datetime, end: datetime) -> list[TimeSlot]
    async def create_event(title: str, start: datetime, end: datetime, attendees: list[str]) -> str
    async def check_conflicts(proposed_time: datetime) -> bool
```

## Features

### Free Slot Detection
- Queries Google Calendar API for busy times in a range
- Computes free slots by subtracting busy periods from work hours
- Configurable work hours (default: 9am-5pm)
- Returns `TimeSlot` objects: `{start, end, duration_minutes}`

### Event Creation
- Creates calendar events with title, time, and attendees
- Sends invitations to all attendees
- Returns calendar event ID for reference

### Conflict Checking
- Checks if a proposed time overlaps with existing events
- Returns boolean + conflicting event details if applicable

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | /calendar/availability | Get free slots for a date range |
| POST | /calendar/events | Create a new calendar event |

## Agent Integration

The calendar tools are registered in the ToolManager:
- `check_calendar` — used by Decision Node for meeting requests
- `create_event` — used by Tool Execution Node to schedule meetings

## Authentication

Uses the same Google OAuth2 tokens as Gmail. Scope required:
- `https://www.googleapis.com/auth/calendar.readonly`
- `https://www.googleapis.com/auth/calendar.events`
