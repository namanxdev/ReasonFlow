"""API routes package — re-exports all route modules."""

from app.api.routes import (
    auth,
    batch,
    calendar,
    crm,
    drafts,
    emails,
    metrics,
    notifications,
    settings,
    templates,
    traces,
)

__all__ = [
    "auth",
    "batch",
    "calendar",
    "crm",
    "drafts",
    "emails",
    "metrics",
    "notifications",
    "settings",
    "templates",
    "traces",
]
