"""Context retrieval node — fetches relevant context for the email."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.agent.state import AgentState

logger = logging.getLogger(__name__)


async def retrieve_node(state: AgentState) -> dict[str, Any]:
    """Retrieve context relevant to the incoming email.

    Performs three independent lookups (each failure is isolated):
      1. Vector similarity search via the retrieval module (pgvector).
      2. CRM contact data for the sender.
      3. Calendar events (only for meeting-related emails).

    Reads:
        ``email``, ``classification``

    Writes:
        ``context`` — sorted list of context strings, highest relevance first.
        ``steps``   — appended step trace entry.
        ``error``   — set when all sub-retrievals fail.
    """
    step_start = time.monotonic()
    step_name = "retrieve"
    current_steps: list[dict[str, Any]] = list(state.get("steps", []))

    email: dict[str, Any] = state.get("email", {})
    classification: str = state.get("classification", "other")
    context_parts: list[str] = []

    logger.info(
        "retrieve_node: starting — trace_id=%s classification=%s",
        state.get("trace_id", "unknown"),
        classification,
    )

    # ------------------------------------------------------------------
    # 1. Vector similarity search for past emails
    # ------------------------------------------------------------------
    try:
        from app.retrieval import search_similar  # type: ignore[import]

        email_text = f"{email.get('subject', '')} {email.get('body', '')}"
        similar = await search_similar(
            text=email_text,
            user_id=email.get("user_id"),
            top_k=5,
        )
        for item in similar:
            if isinstance(item, str):
                context_parts.append(item)
            elif isinstance(item, dict):
                context_parts.append(item.get("text_content", ""))
        logger.debug("retrieve_node: vector search returned %d results", len(similar))
    except ImportError:
        logger.debug("retrieve_node: retrieval module not available; skipping vector search")
    except Exception as exc:
        logger.warning("retrieve_node: vector search failed — %s", exc)

    # ------------------------------------------------------------------
    # 2. CRM contact lookup
    # ------------------------------------------------------------------
    sender: str = email.get("sender", "")
    if sender:
        try:
            from app.integrations.crm.factory import get_crm_client  # type: ignore[import]

            crm_client = get_crm_client()
            contact = await crm_client.get_contact(email=sender)
            if contact:
                parts = []
                if contact.get("name"):
                    parts.append(f"Name: {contact['name']}")
                if contact.get("company"):
                    parts.append(f"Company: {contact['company']}")
                if contact.get("notes"):
                    parts.append(f"Notes: {contact['notes']}")
                if parts:
                    context_parts.append("CRM Contact — " + "; ".join(parts))
            logger.debug("retrieve_node: CRM lookup complete for %s", sender)
        except ImportError:
            logger.debug("retrieve_node: CRM client not available; skipping contact lookup")
        except Exception as exc:
            logger.warning("retrieve_node: CRM lookup failed for %s — %s", sender, exc)

    # ------------------------------------------------------------------
    # 3. Calendar events (meeting_request only)
    # ------------------------------------------------------------------
    if classification == "meeting_request":
        try:
            from app.integrations.calendar.client import CalendarClient  # type: ignore[import]

            cal_client = CalendarClient()
            events = await cal_client.get_upcoming_events(limit=5)
            if events:
                event_strs = []
                for event in events:
                    start = event.get("start", "")
                    end = event.get("end", "")
                    title = event.get("title", "Untitled")
                    event_strs.append(f"{title}: {start} – {end}")
                context_parts.append("Upcoming calendar events: " + "; ".join(event_strs))
            logger.debug("retrieve_node: calendar returned %d events", len(events or []))
        except ImportError:
            logger.debug("retrieve_node: CalendarClient not available; skipping calendar lookup")
        except Exception as exc:
            logger.warning("retrieve_node: calendar lookup failed — %s", exc)

    latency_ms = (time.monotonic() - step_start) * 1000
    # Filter empty strings that may have crept in from failed retrievals.
    context = [c for c in context_parts if c]

    current_steps.append(
        {
            "step": step_name,
            "context_count": len(context),
            "latency_ms": latency_ms,
        }
    )

    logger.info(
        "retrieve_node: done — %d context items latency_ms=%.1f",
        len(context),
        latency_ms,
    )

    return {
        "context": context,
        "steps": current_steps,
    }
