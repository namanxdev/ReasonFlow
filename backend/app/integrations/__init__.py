"""Integrations package for external service clients."""

from __future__ import annotations

from app.integrations.calendar.client import CalendarClient
from app.integrations.crm.factory import get_crm_client
from app.integrations.gmail.client import GmailClient

__all__ = [
    "CalendarClient",
    "GmailClient",
    "get_crm_client",
]
