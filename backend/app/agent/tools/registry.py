"""Tool registry for the ReasonFlow agent.

Each tool is an async callable that accepts a dict of parameters and
returns a dict result.  Tools are registered by name so the decision
and execution nodes can look them up dynamically.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from app.core.security import decrypt_oauth_token

logger = logging.getLogger(__name__)

# Type alias for an async tool callable.
ToolFn = Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]


async def _get_credentials_from_user_id(user_id: str) -> dict[str, Any] | None:
    """Fetch and decrypt user OAuth credentials from the database.

    Returns a dict with 'access_token' and optionally 'refresh_token',
    or None if the user has no OAuth credentials.
    """
    import uuid

    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.database import async_session_factory
    from app.models.user import User

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        logger.warning("Invalid user_id format: %s", user_id)
        return None

    async with async_session_factory() as db:
        try:
            result = await db.execute(select(User).where(User.id == user_uuid))
            user = result.scalar_one_or_none()

            if user is None or not user.oauth_token_encrypted:
                return None

            credentials: dict[str, Any] = {}

            try:
                credentials["access_token"] = decrypt_oauth_token(user.oauth_token_encrypted)
            except ValueError as exc:
                logger.warning("Failed to decrypt access token for user=%s: %s", user_id, exc)
                return None

            if user.oauth_refresh_token_encrypted:
                try:
                    credentials["refresh_token"] = decrypt_oauth_token(
                        user.oauth_refresh_token_encrypted
                    )
                except ValueError:
                    logger.warning("Failed to decrypt refresh token for user=%s", user_id)

            return credentials
        except Exception as exc:
            logger.warning("Failed to get user credentials for user=%s: %s", user_id, exc)
            return None

# Internal registry: tool_name -> async callable.
_registry: dict[str, ToolFn] = {}


def register(name: str) -> Callable[[ToolFn], ToolFn]:
    """Decorator that registers an async function as a named tool.

    Usage::

        @register("send_email")
        async def send_email(params: dict) -> dict:
            ...
    """

    def decorator(fn: ToolFn) -> ToolFn:
        if name in _registry:
            logger.warning("Tool %r is being re-registered; overwriting previous entry.", name)
        _registry[name] = fn
        logger.debug("Registered tool: %s", name)
        return fn

    return decorator


def get_tool(name: str) -> ToolFn | None:
    """Return the callable for *name*, or None if it is not registered."""
    return _registry.get(name)


def list_tools() -> list[str]:
    """Return a sorted list of all registered tool names."""
    return sorted(_registry.keys())


# ---------------------------------------------------------------------------
# Built-in tool implementations
# ---------------------------------------------------------------------------
# These are intentionally thin stubs that integrate with the real external
# service clients when they are available.  Each implementation imports its
# client lazily inside the function body so that the registry module can be
# imported without triggering heavy side-effects or credential checks at
# import time.
# ---------------------------------------------------------------------------


@register("send_email")
async def send_email(params: dict[str, Any]) -> dict[str, Any]:
    """Send an email via Gmail.

    Expected params:
        to (str): Recipient address.
        subject (str): Email subject.
        body (str): Email body text.
        thread_id (str, optional): Gmail thread to reply in.
        user_id (str): User ID for OAuth credentials.
    """
    try:
        # Lazy import to avoid circular / missing dependency errors at load time.
        from app.integrations.gmail.client import GmailClient  # type: ignore[import]

        user_id = params.get("user_id")
        if not user_id:
            raise ValueError("user_id is required for send_email tool")

        credentials = await _get_credentials_from_user_id(user_id)
        if credentials is None:
            raise RuntimeError("User has no valid Gmail OAuth credentials")

        client = GmailClient(credentials=credentials)
        result = await client.send_email(
            to=params.get("to", ""),
            subject=params.get("subject", ""),
            body=params.get("body", ""),
            thread_id=params.get("thread_id"),
        )
        return {"status": "sent", "message_id": result.get("id", "")}
    except ImportError:
        logger.warning("GmailClient not available; send_email tool is a no-op.")
        return {"status": "skipped", "reason": "GmailClient not available"}
    except Exception as exc:
        logger.exception("send_email tool failed: %s", exc)
        raise


@register("create_draft")
async def create_draft(params: dict[str, Any]) -> dict[str, Any]:
    """Create a Gmail draft for human review.

    Expected params:
        to (str): Recipient address.
        subject (str): Email subject.
        body (str): Draft body text.
        thread_id (str, optional): Gmail thread to reply in.
        user_id (str): User ID for OAuth credentials.
    """
    try:
        from app.integrations.gmail.client import GmailClient  # type: ignore[import]

        user_id = params.get("user_id")
        if not user_id:
            raise ValueError("user_id is required for create_draft tool")

        credentials = await _get_credentials_from_user_id(user_id)
        if credentials is None:
            raise RuntimeError("User has no valid Gmail OAuth credentials")

        client = GmailClient(credentials=credentials)
        result = await client.create_draft(
            to=params.get("to", ""),
            subject=params.get("subject", ""),
            body=params.get("body", ""),
            thread_id=params.get("thread_id"),
        )
        return {"status": "drafted", "draft_id": result.get("id", "")}
    except ImportError:
        logger.warning("GmailClient not available; create_draft tool is a no-op.")
        return {"status": "skipped", "reason": "GmailClient not available"}
    except Exception as exc:
        logger.exception("create_draft tool failed: %s", exc)
        raise


@register("check_calendar")
async def check_calendar(params: dict[str, Any]) -> dict[str, Any]:
    """Check calendar availability.

    Expected params:
        start (str): ISO-8601 start datetime.
        end (str): ISO-8601 end datetime.
        timezone (str, optional): IANA timezone string.
    """
    try:
        from app.integrations.calendar.client import CalendarClient  # type: ignore[import]

        client = CalendarClient()
        slots = await client.check_availability(
            start=params.get("start", ""),
            end=params.get("end", ""),
            timezone=params.get("timezone", "UTC"),
        )
        return {"available_slots": slots}
    except ImportError:
        logger.warning("CalendarClient not available; check_calendar tool is a no-op.")
        return {"available_slots": [], "reason": "CalendarClient not available"}
    except Exception as exc:
        logger.exception("check_calendar tool failed: %s", exc)
        raise


@register("create_event")
async def create_event(params: dict[str, Any]) -> dict[str, Any]:
    """Create a calendar event.

    Expected params:
        title (str): Event title.
        start (str): ISO-8601 start datetime.
        end (str): ISO-8601 end datetime.
        attendees (list[str]): Attendee email addresses.
        description (str, optional): Event description.
    """
    try:
        from app.integrations.calendar.client import CalendarClient  # type: ignore[import]

        client = CalendarClient()
        event = await client.create_event(
            title=params.get("title", "Meeting"),
            start=params.get("start", ""),
            end=params.get("end", ""),
            attendees=params.get("attendees", []),
            description=params.get("description", ""),
        )
        return {"status": "created", "event_id": event.get("id", "")}
    except ImportError:
        logger.warning("CalendarClient not available; create_event tool is a no-op.")
        return {"status": "skipped", "reason": "CalendarClient not available"}
    except Exception as exc:
        logger.exception("create_event tool failed: %s", exc)
        raise


@register("get_contact")
async def get_contact(params: dict[str, Any]) -> dict[str, Any]:
    """Fetch CRM contact information.

    Expected params:
        email (str): Contact email address to look up.
    """
    try:
        from app.integrations.crm.factory import get_crm_client  # type: ignore[import]

        client = get_crm_client()
        contact = await client.get_contact(email=params.get("email", ""))
        return contact if contact else {"status": "not_found"}
    except ImportError:
        logger.warning("CRM client not available; get_contact tool is a no-op.")
        return {"status": "skipped", "reason": "CRM client not available"}
    except Exception as exc:
        logger.exception("get_contact tool failed: %s", exc)
        raise


@register("update_contact")
async def update_contact(params: dict[str, Any]) -> dict[str, Any]:
    """Update CRM contact data.

    Expected params:
        email (str): Contact email address.
        fields (dict): Fields to update.
    """
    try:
        from app.integrations.crm.factory import get_crm_client  # type: ignore[import]

        client = get_crm_client()
        result = await client.update_contact(
            email=params.get("email", ""),
            fields=params.get("fields", {}),
        )
        return {"status": "updated", "contact": result}
    except ImportError:
        logger.warning("CRM client not available; update_contact tool is a no-op.")
        return {"status": "skipped", "reason": "CRM client not available"}
    except Exception as exc:
        logger.exception("update_contact tool failed: %s", exc)
        raise
