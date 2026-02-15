"""ContextBuilder — aggregates context from multiple sources for email processing."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.calendar.client import CalendarClient
from app.integrations.crm.factory import get_crm_client
from app.retrieval.embeddings import EmbeddingService
from app.retrieval.vector_store import PgVectorStore

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Builds a rich context dict for the agent pipeline from multiple sources.

    Orchestrates three independent retrievals for each incoming email:

    1. **Similar past emails** — vector similarity search via
       :class:`~app.retrieval.vector_store.PgVectorStore`.
    2. **CRM contact data** — fetched from the active CRM adapter for the
       sender's email address.
    3. **Upcoming calendar events** — only for ``meeting_request``-classified
       emails.

    Each sub-retrieval is isolated; a failure in one does not prevent the
    others from running.

    Usage::

        builder = ContextBuilder()
        ctx = await builder.build_context(email=email_dict, user_id=uid, db_session=session)
    """

    def __init__(
        self,
        embedding_service: EmbeddingService | None = None,
        vector_store: PgVectorStore | None = None,
        similar_limit: int = 5,
        similarity_threshold: float = 0.7,
    ) -> None:
        self._embedding_service = embedding_service or EmbeddingService()
        self._vector_store = vector_store or PgVectorStore()
        self._similar_limit = similar_limit
        self._similarity_threshold = similarity_threshold

    async def build_context(
        self,
        email: dict[str, Any],
        user_id: Any,
        db_session: AsyncSession,
    ) -> dict[str, Any]:
        """Build and return a structured context dictionary.

        Args:
            email:      Dict with at minimum ``subject``, ``body``, and
                        ``sender`` keys.  ``classification`` is optional and
                        used to decide whether to fetch calendar events.
            user_id:    UUID (or string representation) of the owning user,
                        used to scope vector search results.
            db_session: SQLAlchemy async session for database queries.

        Returns:
            A dict with the following keys:

            - ``similar_emails`` (list[dict]): Top-k similar past emails from
              vector store.  Each item has ``text_content``, ``source_id``,
              ``similarity``, and ``metadata``.
            - ``crm_contact`` (dict | None): CRM record for the sender, or
              ``None`` if not found or CRM unavailable.
            - ``calendar_events`` (list[dict]): Upcoming calendar events.
              Empty list when email is not a ``meeting_request`` or calendar
              is unavailable.
            - ``context_strings`` (list[str]): Pre-formatted strings ready for
              inclusion in an LLM prompt, aggregated from all three sources.
        """
        subject: str = email.get("subject", "")
        body: str = email.get("body", "")
        sender: str = email.get("sender", "")
        classification: str = email.get("classification", "other")

        similar_emails: list[dict[str, Any]] = []
        crm_contact: dict[str, Any] | None = None
        calendar_events: list[dict[str, Any]] = []

        # ------------------------------------------------------------------
        # 1. Similar past emails via vector search
        # ------------------------------------------------------------------
        email_text = f"{subject} {body}".strip()
        if email_text:
            try:
                query_embedding = await self._embedding_service.create_embedding(
                    email_text
                )
                similar_emails = await self._vector_store.search_similar(
                    query_embedding=query_embedding,
                    user_id=user_id,
                    limit=self._similar_limit,
                    threshold=self._similarity_threshold,
                    source_type="email",
                    db=db_session,
                )
                logger.debug(
                    "ContextBuilder.build_context: vector search returned %d results",
                    len(similar_emails),
                )
            except Exception as exc:
                logger.warning(
                    "ContextBuilder.build_context: vector search failed — %s", exc
                )

        # ------------------------------------------------------------------
        # 2. CRM contact data
        # ------------------------------------------------------------------
        if sender:
            try:
                crm_client = get_crm_client()
                crm_contact = await crm_client.get_contact(email=sender)
                logger.debug(
                    "ContextBuilder.build_context: CRM lookup for %s found=%s",
                    sender,
                    crm_contact is not None,
                )
            except Exception as exc:
                logger.warning(
                    "ContextBuilder.build_context: CRM lookup failed for %s — %s",
                    sender,
                    exc,
                )

        # ------------------------------------------------------------------
        # 3. Upcoming calendar events (meeting_request emails only)
        # ------------------------------------------------------------------
        if classification == "meeting_request":
            try:
                # CalendarClient requires OAuth credentials; in environments
                # where they are not available this will raise and be caught.
                credentials: dict[str, Any] = email.get("user_credentials", {})
                if credentials:
                    cal_client = CalendarClient(credentials=credentials)
                    free_slots = await cal_client.get_free_slots(
                        target_date=date.today()
                    )
                    calendar_events = free_slots
                    logger.debug(
                        "ContextBuilder.build_context: calendar returned %d free slots",
                        len(calendar_events),
                    )
                else:
                    logger.debug(
                        "ContextBuilder.build_context: no credentials for calendar lookup"
                    )
            except Exception as exc:
                logger.warning(
                    "ContextBuilder.build_context: calendar lookup failed — %s", exc
                )

        # ------------------------------------------------------------------
        # Build human-readable context strings for LLM prompts
        # ------------------------------------------------------------------
        context_strings = _build_context_strings(
            similar_emails=similar_emails,
            crm_contact=crm_contact,
            calendar_events=calendar_events,
        )

        logger.info(
            "ContextBuilder.build_context: built %d context strings "
            "(similar=%d crm=%s calendar=%d)",
            len(context_strings),
            len(similar_emails),
            crm_contact is not None,
            len(calendar_events),
        )

        return {
            "similar_emails": similar_emails,
            "crm_contact": crm_contact,
            "calendar_events": calendar_events,
            "context_strings": context_strings,
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_context_strings(
    similar_emails: list[dict[str, Any]],
    crm_contact: dict[str, Any] | None,
    calendar_events: list[dict[str, Any]],
) -> list[str]:
    """Format retrieved context as strings suitable for LLM prompt injection."""
    parts: list[str] = []

    for idx, item in enumerate(similar_emails, start=1):
        text = item.get("text_content", "").strip()
        similarity = item.get("similarity", 0.0)
        if text:
            parts.append(
                f"[Past email {idx} (similarity={similarity:.2f})]: {text}"
            )

    if crm_contact:
        crm_parts: list[str] = []
        if crm_contact.get("name"):
            crm_parts.append(f"Name: {crm_contact['name']}")
        if crm_contact.get("company"):
            crm_parts.append(f"Company: {crm_contact['company']}")
        if crm_contact.get("title"):
            crm_parts.append(f"Title: {crm_contact['title']}")
        if crm_contact.get("notes"):
            crm_parts.append(f"Notes: {crm_contact['notes']}")
        if crm_contact.get("tags"):
            crm_parts.append(f"Tags: {', '.join(crm_contact['tags'])}")
        if crm_parts:
            parts.append("CRM Contact — " + "; ".join(crm_parts))

    if calendar_events:
        event_strs: list[str] = []
        for event in calendar_events:
            start = event.get("start", "")
            end = event.get("end", "")
            title = event.get("title") or event.get("summary", "Untitled")
            event_strs.append(f"{title}: {start} – {end}")
        parts.append("Upcoming calendar events: " + "; ".join(event_strs))

    return parts
