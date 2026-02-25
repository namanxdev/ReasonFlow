"""Task tracker for graceful shutdown of background tasks.

This module provides a way to track and gracefully shutdown background tasks
when the application receives a shutdown signal.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class TaskTracker:
    """Track active background tasks for graceful shutdown.

    This class provides a registry for background tasks that need to complete
    before the application shuts down. It's designed to work with FastAPI's
    lifespan context manager.

    Example:
        >>> tracker = TaskTracker()
        >>>
        >>> # In lifespan startup
        >>> app.state.task_tracker = tracker
        >>>
        >>> # In background task
        >>> tracker.add_task(asyncio.create_task(my_coro()))
        >>>
        >>> # In lifespan shutdown
        >>> await tracker.wait_for_completion(timeout=30.0)
    """

    def __init__(self) -> None:
        """Initialize the task tracker."""
        self._tasks: set[asyncio.Task[Any]] = set()
        self._shutdown_event = asyncio.Event()

    def add_task(self, task: asyncio.Task[Any]) -> None:
        """Add a task to be tracked.

        Args:
            task: The asyncio task to track
        """
        self._tasks.add(task)
        task.add_done_callback(self._remove_task)
        logger.debug("Added task %s to tracker, total tasks: %d", task.get_name(), len(self._tasks))

    def _remove_task(self, task: asyncio.Task[Any]) -> None:
        """Remove a task from tracking when it completes.

        This is called as a callback when a task completes.
        """
        self._tasks.discard(task)
        logger.debug(
            "Removed completed task %s from tracker, remaining: %d",
            task.get_name(), len(self._tasks),
        )

    async def wait_for_completion(self, timeout: float | None = 30.0) -> bool:
        """Wait for all tracked tasks to complete.

        Args:
            timeout: Maximum time to wait in seconds. None means wait indefinitely.

        Returns:
            True if all tasks completed, False if timeout occurred.

        Note:
            This should be called during application shutdown in the lifespan
            handler. It gives background tasks a chance to complete gracefully.
        """
        if not self._tasks:
            logger.info("No active background tasks to wait for")
            return True

        logger.info(
            "Waiting for %d background tasks to complete (timeout=%s)",
            len(self._tasks), timeout,
        )

        # Create a task that waits for all tracked tasks
        all_tasks = asyncio.gather(*self._tasks, return_exceptions=True)

        try:
            if timeout is not None:
                await asyncio.wait_for(all_tasks, timeout=timeout)
            else:
                await all_tasks
            logger.info("All background tasks completed gracefully")
            return True
        except TimeoutError:
            # Get remaining tasks
            remaining = [t for t in self._tasks if not t.done()]
            logger.warning(
                "Timeout waiting for background tasks. %d tasks still running: %s",
                len(remaining),
                [t.get_name() for t in remaining]
            )

            # Cancel remaining tasks
            for task in remaining:
                task.cancel()
                logger.debug("Cancelled task %s", task.get_name())

            # Wait a short time for cancellation to take effect
            try:
                await asyncio.wait_for(
                    asyncio.gather(*remaining, return_exceptions=True),
                    timeout=5.0
                )
            except TimeoutError:
                logger.error("Some tasks did not respond to cancellation")

            return False

    def get_active_tasks(self) -> list[asyncio.Task[Any]]:
        """Get a list of currently active (non-done) tasks.

        Returns:
            List of active asyncio tasks
        """
        return [t for t in self._tasks if not t.done()]

    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested.

        Returns:
            True if shutdown event is set
        """
        return self._shutdown_event.is_set()

    def request_shutdown(self) -> None:
        """Request shutdown, signaling tasks to stop.

        Background tasks can check is_shutdown_requested() to cooperatively
        stop processing when shutdown is requested.
        """
        logger.info("Shutdown requested, signaling background tasks")
        self._shutdown_event.set()


# Global task tracker instance
task_tracker = TaskTracker()


def get_task_tracker() -> TaskTracker:
    """Get the global task tracker instance.

    Returns:
        The global TaskTracker instance
    """
    return task_tracker
