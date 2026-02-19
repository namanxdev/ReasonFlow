"""Settings/Preferences business logic."""

from __future__ import annotations

import logging
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_preferences import UserPreferences
from app.schemas.settings import UserPreferencesUpdateRequest

logger = logging.getLogger(__name__)


def _get_default_notification_settings() -> dict:
    """Return default notification settings."""
    return {
        "email": True,
        "push": False,
        "digest": True,
    }


async def get_preferences(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> UserPreferences:
    """Get or create user preferences for the given user.

    If preferences don't exist for the user, creates default preferences.

    Args:
        db: Database session
        user_id: User identifier

    Returns:
        UserPreferences model instance
    """
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == user_id)
    )
    preferences: UserPreferences | None = result.scalars().first()

    if preferences is None:
        # Create default preferences for the user
        preferences = UserPreferences(
            user_id=user_id,
            auto_approval_threshold=0.9,
            email_sync_frequency_minutes=15,
            notification_settings=_get_default_notification_settings(),
            timezone="UTC",
            daily_digest_enabled=True,
            auto_classify_on_sync=True,
            max_auto_responses_per_day=50,
        )
        db.add(preferences)
        await db.flush()
        await db.refresh(preferences)
        logger.info("Created default preferences for user=%s", user_id)

    return preferences


async def update_preferences(
    db: AsyncSession,
    user_id: uuid.UUID,
    updates: UserPreferencesUpdateRequest,
) -> UserPreferences:
    """Update user preferences with partial updates.

    Only fields that are not None in the update request will be modified.

    Args:
        db: Database session
        user_id: User identifier
        updates: Partial update request containing fields to modify

    Returns:
        Updated UserPreferences model instance
    """
    # Get or create preferences first
    preferences = await get_preferences(db, user_id)

    # Update only provided fields
    update_data = updates.model_dump(exclude_unset=True, exclude_none=True)

    for field, value in update_data.items():
        setattr(preferences, field, value)

    await db.flush()
    await db.refresh(preferences)

    logger.info("Updated preferences for user=%s: %s", user_id, list(update_data.keys()))
    return preferences
