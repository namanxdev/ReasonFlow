"""Background email sync scheduler.

Periodically syncs and auto-classifies emails for all connected users.
"""

from __future__ import annotations

import asyncio
import logging

from sqlalchemy import select

from app.core.database import async_session_factory
from app.core.events import EventType, publish_event
from app.models.user import User
from app.services.email_service import _sync_emails_core, classify_unclassified_emails

logger = logging.getLogger(__name__)

_scheduler_task: asyncio.Task | None = None

SYNC_INTERVAL_SECONDS = 180  # 3 minutes
INITIAL_DELAY_SECONDS = 30


async def _sync_all_users() -> None:
    """Sync emails for every user that has connected Gmail."""
    async with async_session_factory() as db:
        result = await db.execute(
            select(User).where(User.oauth_token_encrypted.isnot(None))
        )
        users = list(result.scalars().all())

    if not users:
        logger.debug("Scheduler: no users with Gmail connected, skipping sync.")
        return

    logger.info("Scheduler: syncing %d user(s).", len(users))

    for user in users:
        try:
            async with async_session_factory() as db:
                sync_result = await _sync_emails_core(db, user) or {}
                await db.commit()

                # Auto-classify if new emails were found
                if sync_result.get("created", 0) > 0:
                    async with async_session_factory() as classify_db:
                        classify_result = await classify_unclassified_emails(classify_db, user.id)
                        await classify_db.commit()
                        logger.info(
                            "Scheduler: auto-classified %d emails for user=%s",
                            classify_result.get("classified", 0),
                            user.id,
                        )

                # Publish sync complete event
                await publish_event(
                    user_id=user.id,
                    event_type=EventType.EMAIL_SYNC_COMPLETE,
                    data={
                        "fetched": sync_result.get("fetched", 0),
                        "created": sync_result.get("created", 0),
                    },
                )

        except Exception as exc:
            logger.warning(
                "Scheduler: sync failed for user=%s: %s",
                user.id,
                exc,
            )


async def _scheduler_loop() -> None:
    """Infinite loop that runs email sync every SYNC_INTERVAL_SECONDS."""
    logger.info(
        "Scheduler: starting (initial_delay=%ds, interval=%ds).",
        INITIAL_DELAY_SECONDS,
        SYNC_INTERVAL_SECONDS,
    )
    await asyncio.sleep(INITIAL_DELAY_SECONDS)

    while True:
        try:
            await _sync_all_users()
        except Exception as exc:
            logger.error("Scheduler: unexpected error in sync loop: %s", exc)

        await asyncio.sleep(SYNC_INTERVAL_SECONDS)


def start_scheduler() -> None:
    """Start the background scheduler task."""
    global _scheduler_task
    if _scheduler_task is not None:
        logger.warning("Scheduler: already running, ignoring start request.")
        return
    _scheduler_task = asyncio.create_task(_scheduler_loop())
    logger.info("Scheduler: background task created.")


async def stop_scheduler() -> None:
    """Stop the background scheduler task."""
    global _scheduler_task
    if _scheduler_task is None:
        return
    _scheduler_task.cancel()
    try:
        await _scheduler_task
    except asyncio.CancelledError:
        pass
    _scheduler_task = None
    logger.info("Scheduler: stopped.")
