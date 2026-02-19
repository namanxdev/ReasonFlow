"""Business logic services package."""

from app.services import batch_service, health_service, template_service
from app.services.auth_service import (
    handle_gmail_callback,
    login,
    refresh_token,
    register,
)
from app.services.draft_service import (
    approve_draft,
    edit_draft,
    list_drafts,
    reject_draft,
)
from app.services.email_service import (
    get_email,
    list_emails,
    process_email,
    sync_emails,
)
from app.services.metrics_service import (
    get_intent_distribution,
    get_latency_metrics,
    get_tool_metrics,
)
from app.services.settings_service import (
    get_preferences,
    update_preferences,
)
from app.services.trace_service import (
    get_trace_detail,
    list_traces,
)

__all__ = [
    # batch
    "batch_service",
    # auth
    "register",
    "login",
    "refresh_token",
    "handle_gmail_callback",
    # email
    "list_emails",
    "get_email",
    "sync_emails",
    "process_email",
    # draft
    "list_drafts",
    "approve_draft",
    "reject_draft",
    "edit_draft",
    # metrics
    "get_intent_distribution",
    "get_latency_metrics",
    "get_tool_metrics",
    # trace
    "list_traces",
    "get_trace_detail",
    # settings
    "get_preferences",
    "update_preferences",
    # health
    "health_service",
    # templates
    "template_service",
]
