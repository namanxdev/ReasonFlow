"""Event publishing and subscription for real-time notifications."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING
from uuid import UUID

from app.core.redis import get_redis_client

if TYPE_CHECKING:
    from redis.asyncio import Redis

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


async def publish_event(user_id: UUID, event_type: EventType, data: dict) -> None:
    """Publish event to Redis pub/sub channel.

    Args:
        user_id: The user ID to publish the event for.
        event_type: The type of event being published.
        data: Event payload data.
    """
    try:
        redis: Redis = await get_redis_client()
        event = {
            "type": event_type.value,
            "user_id": str(user_id),
            "data": data,
            "timestamp": datetime.now(UTC).isoformat(),
        }
        channel = f"events:{user_id}"
        await redis.publish(channel, json.dumps(event))
        logger.debug("Published event %s to channel %s", event_type.value, channel)
    except Exception as exc:
        # Log but don't raise - notifications should not break core functionality
        logger.warning("Failed to publish event %s for user %s: %s", event_type.value, user_id, exc)


async def subscribe_events(user_id: UUID):
    """Subscribe to events for a user - async generator.

    Args:
        user_id: The user ID to subscribe to events for.

    Yields:
        dict: Parsed event data from Redis pub/sub messages.
    """
    redis: Redis = await get_redis_client()
    pubsub = redis.pubsub()
    channel = f"events:{user_id}"
    await pubsub.subscribe(channel)
    logger.info("Subscribed to events channel: %s", channel)

    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    event_data = json.loads(message["data"])
                    yield event_data
                except json.JSONDecodeError as exc:
                    logger.warning("Failed to decode event message: %s", exc)
    finally:
        await pubsub.unsubscribe(channel)
        logger.info("Unsubscribed from events channel: %s", channel)
