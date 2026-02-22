"""Database models package."""

from app.models.agent_log import AgentLog
from app.models.base import Base
from app.models.email import Email, EmailClassification, EmailStatus
from app.models.email_template import EmailTemplate
from app.models.embedding import Embedding
from app.models.idempotency_key import IdempotencyKey
from app.models.tool_execution import ToolExecution
from app.models.user import User
from app.models.user_preferences import UserPreferences

__all__ = [
    "Base",
    "User",
    "UserPreferences",
    "Email",
    "EmailClassification",
    "EmailStatus",
    "AgentLog",
    "IdempotencyKey",
    "ToolExecution",
    "Embedding",
    "EmailTemplate",
]
