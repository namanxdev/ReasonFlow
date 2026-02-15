"""In-memory MockCRM implementation for development and testing."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.integrations.crm.base import CRMBase

logger = logging.getLogger(__name__)

_SEED_CONTACTS: list[dict[str, Any]] = [
    {
        "email": "alice@example.com",
        "name": "Alice Smith",
        "company": "Acme Corp",
        "title": "VP of Engineering",
        "last_interaction": "2026-01-20T10:00:00Z",
        "notes": "Interested in enterprise plan",
        "tags": ["prospect", "enterprise"],
    },
    {
        "email": "bob@techcorp.io",
        "name": "Bob Johnson",
        "company": "TechCorp",
        "title": "CTO",
        "last_interaction": "2026-01-15T14:30:00Z",
        "notes": "Evaluating for Q2 rollout",
        "tags": ["prospect"],
    },
    {
        "email": "carol@startup.dev",
        "name": "Carol Williams",
        "company": "Startup Dev",
        "title": "Founder",
        "last_interaction": "2026-02-01T09:00:00Z",
        "notes": "Signed up for beta",
        "tags": ["customer", "beta"],
    },
]


class MockCRM(CRMBase):
    """In-memory CRM with sample contacts for development and demos."""

    def __init__(self) -> None:
        self._contacts: dict[str, dict[str, Any]] = {
            contact["email"]: dict(contact) for contact in _SEED_CONTACTS
        }

    async def get_contact(self, email: str) -> dict[str, Any] | None:
        contact = self._contacts.get(email)
        if contact is None:
            logger.debug("MockCRM: contact not found for email=%s", email)
            return None
        return dict(contact)

    async def update_contact(self, email: str, data: dict[str, Any]) -> dict[str, Any]:
        existing = self._contacts.get(email, {"email": email})
        existing.update(data)
        existing["email"] = email
        existing["last_interaction"] = datetime.now(tz=timezone.utc).isoformat()
        self._contacts[email] = existing
        logger.debug("MockCRM: updated contact email=%s", email)
        return dict(existing)

    async def search_contacts(self, query: str) -> list[dict[str, Any]]:
        q = query.lower()
        results = []
        for contact in self._contacts.values():
            searchable = " ".join(
                str(contact.get(field, ""))
                for field in ("name", "email", "company", "title", "notes")
            ).lower()
            if q in searchable:
                results.append(dict(contact))
        logger.debug("MockCRM: search query=%r returned %d results", query, len(results))
        return results
