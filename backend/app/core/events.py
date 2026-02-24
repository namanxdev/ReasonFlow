"""Event publishing and subscription for real-time notifications.

Uses an in-memory async event bus (asyncio.Queue per subscriber).
Suitable for single-server MVP deployments. State resets on server restart.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

logger = logging.getLogger(__name__)


class EventType(StrEnum):
    """Event types for real-time notifications."""

    EMAIL_RECEIVED = "email_received"
    EMAIL_CLASSIFIED = "email_classified"
    DRAFT_READY = "draft_ready"
    DRAFT_APPROVED = "draft_approved"
    DRAFT_REJECTED = "draft_rejected"
    EMAIL_SENT = "email_sent"
    BATCH_PROGRESS = "batch_progress"
    BATCH_COMPLETE = "batch_complete"
    EMAIL_SYNC_COMPLETE = "email_sync_complete"


# In-memory subscriber registry: {user_id: [asyncio.Queue, ...]}
_subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)


async def publish_event(user_id: UUID, event_type: EventType, data: dict) -> None:
    """Publish event to all in-memory subscribers for a user.

    Args:
        user_id: The user ID to publish the event for.
        event_type: The type of event being published.
        data: Event payload data.
    """
    try:
        event = {
            "type": event_type.value,
            "user_id": str(user_id),
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        channel = str(user_id)
        queues = _subscribers.get(channel, [])
        for queue in queues:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning("Event queue full for user %s, dropping event", user_id)
        if queues:
            logger.debug("Published event %s to %d subscribers for user %s", event_type.value, len(queues), user_id)
    except Exception as exc:
        # Log but don't raise - notifications should not break core functionality
        logger.warning("Failed to publish event %s for user %s: %s", event_type.value, user_id, exc)


async def subscribe_events(user_id: UUID):
    """Subscribe to events for a user - async generator.

    Args:
        user_id: The user ID to subscribe to events for.

    Yields:
        dict: Parsed event data from the in-memory event bus.
    """
    channel = str(user_id)
    queue: asyncio.Queue = asyncio.Queue(maxsize=100)
    _subscribers[channel].append(queue)
    logger.info("Subscribed to events for user: %s", user_id)

    try:
        while True:
            event_data = await queue.get()
            yield event_data
    finally:
        _subscribers[channel].remove(queue)
        if not _subscribers[channel]:
            del _subscribers[channel]
        logger.info("Unsubscribed from events for user: %s", user_id)
