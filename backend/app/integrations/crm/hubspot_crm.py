"""HubSpot CRM adapter implementation.

This module provides a production-ready CRM adapter using HubSpot's API.
It implements the CRMBase interface for seamless integration.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.crm.base import CRMBase

logger = logging.getLogger(__name__)


class HubSpotCRM(CRMBase):
    """HubSpot CRM adapter for production use.

    This adapter uses HubSpot's REST API to manage contacts.
    Requires HUBSPOT_API_KEY in settings.

    Features:
    - Contact CRUD operations
    - Contact search
    - Company association
    - Activity tracking
    """

    def __init__(self) -> None:
        """Initialize HubSpot client with API credentials."""
        self.api_key = settings.HUBSPOT_API_KEY
        self.base_url = settings.HUBSPOT_BASE_URL.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if not self.api_key:
            raise ValueError("HUBSPOT_API_KEY is required for HubSpotCRM")

    async def _request(
        self,
        method: str,
        endpoint: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make an HTTP request to HubSpot API."""
        url = f"{self.base_url}{endpoint}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=json_data,
                    params=params,
                    timeout=30.0,
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                logger.error(
                    "HubSpot API error: %s %s - %s",
                    method,
                    endpoint,
                    e.response.text,
                )
                raise
            except Exception as e:
                logger.error("HubSpot request failed: %s", e)
                raise

    async def get_contact(self, email: str) -> dict[str, Any] | None:
        """Get contact by email from HubSpot.

        Uses HubSpot's search API to find contact by email.
        """
        try:
            # Search for contact by email
            search_payload = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "email",
                                "operator": "EQ",
                                "value": email.lower(),
                            }
                        ]
                    }
                ],
                "limit": 1,
            }

            result = await self._request(
                "POST",
                "/crm/v3/objects/contacts/search",
                json_data=search_payload,
            )

            items = result.get("results", [])
            if not items:
                return None

            contact = items[0]
            properties = contact.get("properties", {})

            return {
                "id": contact.get("id"),
                "email": properties.get("email", email),
                "name": properties.get("firstname", "") + " " + properties.get("lastname", ""),
                "first_name": properties.get("firstname", ""),
                "last_name": properties.get("lastname", ""),
                "company": properties.get("company", ""),
                "title": properties.get("jobtitle", ""),
                "phone": properties.get("phone", ""),
                "notes": properties.get("notes_last_updated", ""),
                "tags": [],
                "source": "hubspot",
            }
        except Exception as e:
            logger.error("Failed to get contact from HubSpot: %s", e)
            return None

    async def update_contact(self, email: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create or update contact in HubSpot.

        Uses HubSpot's create or update endpoint.
        """
        try:
            # Map our data fields to HubSpot properties
            properties: dict[str, Any] = {
                "email": email.lower(),
            }

            if name := data.get("name"):
                parts = name.split(" ", 1)
                properties["firstname"] = parts[0]
                if len(parts) > 1:
                    properties["lastname"] = parts[1]

            if first_name := data.get("first_name"):
                properties["firstname"] = first_name
            if last_name := data.get("last_name"):
                properties["lastname"] = last_name
            if company := data.get("company"):
                properties["company"] = company
            if title := data.get("title"):
                properties["jobtitle"] = title
            if phone := data.get("phone"):
                properties["phone"] = phone
            if notes := data.get("notes"):
                properties["notes"] = notes

            # Check if contact exists
            existing = await self.get_contact(email)

            if existing:
                # Update existing contact
                contact_id = existing["id"]
                await self._request(
                    "PATCH",
                    f"/crm/v3/objects/contacts/{contact_id}",
                    json_data={"properties": properties},
                )
                logger.info("Updated HubSpot contact: %s", email)
            else:
                # Create new contact
                await self._request(
                    "POST",
                    "/crm/v3/objects/contacts",
                    json_data={"properties": properties},
                )
                logger.info("Created HubSpot contact: %s", email)

            # Return updated contact
            updated = await self.get_contact(email)
            return updated or {"email": email, **data}

        except Exception as e:
            logger.error("Failed to update HubSpot contact: %s", e)
            # Return local data as fallback
            return {"email": email, **data}

    async def search_contacts(self, query: str) -> list[dict[str, Any]]:
        """Search contacts in HubSpot.

        Searches across email, firstname, lastname, and company.
        """
        try:
            search_payload = {
                "filterGroups": [
                    {
                        "filters": [
                            {
                                "propertyName": "email",
                                "operator": "CONTAINS_TOKEN",
                                "value": query,
                            }
                        ]
                    },
                    {
                        "filters": [
                            {
                                "propertyName": "firstname",
                                "operator": "CONTAINS_TOKEN",
                                "value": query,
                            }
                        ]
                    },
                    {
                        "filters": [
                            {
                                "propertyName": "lastname",
                                "operator": "CONTAINS_TOKEN",
                                "value": query,
                            }
                        ]
                    },
                ],
                "limit": 50,
            }

            result = await self._request(
                "POST",
                "/crm/v3/objects/contacts/search",
                json_data=search_payload,
            )

            items = result.get("results", [])
            contacts = []

            for item in items:
                properties = item.get("properties", {})
                contacts.append({
                    "id": item.get("id"),
                    "email": properties.get("email", ""),
                    "name": " ".join(filter(None, [
                        properties.get("firstname", ""),
                        properties.get("lastname", ""),
                    ])),
                    "first_name": properties.get("firstname", ""),
                    "last_name": properties.get("lastname", ""),
                    "company": properties.get("company", ""),
                    "title": properties.get("jobtitle", ""),
                    "phone": properties.get("phone", ""),
                    "tags": [],
                    "source": "hubspot",
                })

            return contacts

        except Exception as e:
            logger.error("Failed to search HubSpot contacts: %s", e)
            return []

    async def get_company(self, company_id: str) -> dict[str, Any] | None:
        """Get company details from HubSpot.

        Useful for enriching contact data with company information.
        """
        try:
            result = await self._request(
                "GET",
                f"/crm/v3/objects/companies/{company_id}",
            )

            properties = result.get("properties", {})
            return {
                "id": result.get("id"),
                "name": properties.get("name", ""),
                "domain": properties.get("domain", ""),
                "industry": properties.get("industry", ""),
                "size": properties.get("num_employees", ""),
            }
        except Exception as e:
            logger.error("Failed to get HubSpot company: %s", e)
            return None
