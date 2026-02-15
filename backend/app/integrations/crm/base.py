"""Abstract base class for CRM adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class CRMBase(ABC):
    """Abstract CRM adapter interface.

    All CRM implementations must implement this interface so the rest of
    the application can remain provider-agnostic.
    """

    @abstractmethod
    async def get_contact(self, email: str) -> dict[str, Any] | None:
        """Return the contact record for the given email, or None if not found."""

    @abstractmethod
    async def update_contact(self, email: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create or update the contact with the provided fields."""

    @abstractmethod
    async def search_contacts(self, query: str) -> list[dict[str, Any]]:
        """Search contacts by name, email, company, or notes."""
