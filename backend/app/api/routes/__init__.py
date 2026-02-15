"""API routes package — re-exports all route modules."""

from app.api.routes import auth, calendar, crm, drafts, emails, metrics, traces

__all__ = [
    "auth",
    "calendar",
    "crm",
    "drafts",
    "emails",
    "metrics",
    "traces",
]
