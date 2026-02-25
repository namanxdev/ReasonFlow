"""Google Calendar API client using httpx and Google OAuth2 credentials."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime
from typing import Any

import httpx

logger = logging.getLogger(__name__)

CALENDAR_API_BASE = "https://www.googleapis.com/calendar/v3"
PRIMARY_CALENDAR = "primary"


class CalendarClient:
    """Async Google Calendar API client backed by Google OAuth2 credentials."""

    def __init__(self, credentials: dict[str, Any]) -> None:
        self._credentials = credentials

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._credentials['access_token']}"}

    async def _refresh_if_needed(self, client: httpx.AsyncClient) -> None:
        from app.core.config import settings

        refresh_token = self._credentials.get("refresh_token")
        if not refresh_token:
            return

        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GMAIL_CLIENT_ID,
                "client_secret": settings.GMAIL_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        if response.status_code == 200:
            self._credentials["access_token"] = response.json()["access_token"]
            logger.debug("Calendar access token refreshed")
        else:
            logger.warning("Failed to refresh Calendar token: %s", response.status_code)

    async def get_free_slots(
        self,
        target_date: date,
        work_hours: tuple[int, int] = (9, 17),
    ) -> list[dict[str, Any]]:
        work_start = datetime(
            target_date.year, target_date.month, target_date.day,
            work_hours[0], 0, 0, tzinfo=UTC,
        )
        work_end = datetime(
            target_date.year, target_date.month, target_date.day,
            work_hours[1], 0, 0, tzinfo=UTC,
        )

        async with httpx.AsyncClient() as client:
            await self._refresh_if_needed(client)
            response = await client.post(
                f"{CALENDAR_API_BASE}/freeBusy",
                headers={**self._auth_headers(), "Content-Type": "application/json"},
                json={
                    "timeMin": work_start.isoformat(),
                    "timeMax": work_end.isoformat(),
                    "items": [{"id": PRIMARY_CALENDAR}],
                },
            )
            response.raise_for_status()
            data = response.json()

        busy_periods = (
            data.get("calendars", {}).get(PRIMARY_CALENDAR, {}).get("busy", [])
        )
        busy: list[tuple[datetime, datetime]] = []
        for period in busy_periods:
            start = datetime.fromisoformat(period["start"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(period["end"].replace("Z", "+00:00"))
            busy.append((start, end))

        return _compute_free_slots(work_start, work_end, busy)

    async def create_event(
        self,
        summary: str,
        start: datetime,
        end: datetime,
        attendees: list[str],
    ) -> dict[str, Any]:
        event_body: dict[str, Any] = {
            "summary": summary,
            "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
            "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
            "attendees": [{"email": addr} for addr in attendees],
            "reminders": {"useDefault": True},
        }

        async with httpx.AsyncClient() as client:
            await self._refresh_if_needed(client)
            response = await client.post(
                f"{CALENDAR_API_BASE}/calendars/{PRIMARY_CALENDAR}/events",
                headers={**self._auth_headers(), "Content-Type": "application/json"},
                params={"sendUpdates": "all"},
                json=event_body,
            )
            response.raise_for_status()
            data = response.json()

        logger.info("Calendar event created: id=%s summary=%r", data.get("id"), summary)
        return data

    async def list_events(
        self,
        time_min: datetime,
        time_max: datetime,
        max_results: int = 20,
    ) -> list[dict[str, Any]]:
        """List calendar events within the given range."""
        if time_min.tzinfo is None:
            time_min = time_min.replace(tzinfo=UTC)
        if time_max.tzinfo is None:
            time_max = time_max.replace(tzinfo=UTC)
        async with httpx.AsyncClient() as client:
            await self._refresh_if_needed(client)
            response = await client.get(
                f"{CALENDAR_API_BASE}/calendars/{PRIMARY_CALENDAR}/events",
                headers=self._auth_headers(),
                params={
                    "timeMin": time_min.isoformat(),
                    "timeMax": time_max.isoformat(),
                    "maxResults": max_results,
                    "singleEvents": "true",
                    "orderBy": "startTime",
                },
            )
            response.raise_for_status()
            data = response.json()
        return data.get("items", [])

    async def check_conflicts(self, start: datetime, end: datetime) -> bool:
        async with httpx.AsyncClient() as client:
            await self._refresh_if_needed(client)
            response = await client.post(
                f"{CALENDAR_API_BASE}/freeBusy",
                headers={**self._auth_headers(), "Content-Type": "application/json"},
                json={
                    "timeMin": start.isoformat(),
                    "timeMax": end.isoformat(),
                    "items": [{"id": PRIMARY_CALENDAR}],
                },
            )
            response.raise_for_status()
            data = response.json()

        busy = data.get("calendars", {}).get(PRIMARY_CALENDAR, {}).get("busy", [])
        has_conflict = len(busy) > 0
        if has_conflict:
            logger.debug(
                "Conflict detected between %s and %s: %s busy periods",
                start, end, len(busy),
            )
        return has_conflict


def _compute_free_slots(
    work_start: datetime,
    work_end: datetime,
    busy: list[tuple[datetime, datetime]],
) -> list[dict[str, Any]]:
    clipped: list[tuple[datetime, datetime]] = []
    for b_start, b_end in sorted(busy):
        s = max(b_start, work_start)
        e = min(b_end, work_end)
        if s < e:
            clipped.append((s, e))

    free: list[dict[str, Any]] = []
    cursor = work_start

    for b_start, b_end in clipped:
        if cursor < b_start:
            duration = int((b_start - cursor).total_seconds() / 60)
            free.append({
                "start": cursor.isoformat(),
                "end": b_start.isoformat(),
                "duration_minutes": duration,
            })
        cursor = max(cursor, b_end)

    if cursor < work_end:
        duration = int((work_end - cursor).total_seconds() / 60)
        free.append({
            "start": cursor.isoformat(),
            "end": work_end.isoformat(),
            "duration_minutes": duration,
        })

    return free
