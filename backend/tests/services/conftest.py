"""Fixtures shared across service unit tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.agent_log import AgentLog
from app.models.email import Email, EmailClassification, EmailStatus
from app.models.tool_execution import ToolExecution
from app.models.user import User


# ---------------------------------------------------------------------------
# Database session mock (overrides root conftest for services sub-package)
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_db():
    """Return an AsyncMock SQLAlchemy session with helpers for controlling query results."""
    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.execute = AsyncMock()
    return db


# ---------------------------------------------------------------------------
# Model factories (plain constructors that bypass __init__ validation)
# ---------------------------------------------------------------------------


def make_user(
    *,
    email: str = "test@example.com",
    hashed_password: str = "hashed_pw",
    oauth_token_encrypted: str | None = None,
    oauth_refresh_token_encrypted: str | None = None,
) -> User:
    user = User.__new__(User)
    user.id = uuid.uuid4()
    user.email = email
    user.hashed_password = hashed_password
    user.oauth_token_encrypted = oauth_token_encrypted
    user.oauth_refresh_token_encrypted = oauth_refresh_token_encrypted
    user.emails = []
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


def make_email(
    *,
    user_id: uuid.UUID | None = None,
    gmail_id: str = "gmail-abc",
    subject: str = "Hello",
    sender: str = "alice@example.com",
    body: str = "Body text",
    status: EmailStatus = EmailStatus.PENDING,
    classification: EmailClassification | None = None,
    confidence: float | None = None,
    draft_response: str | None = None,
) -> Email:
    email = Email.__new__(Email)
    email.id = uuid.uuid4()
    email.user_id = user_id or uuid.uuid4()
    email.gmail_id = gmail_id
    email.thread_id = "thread-1"
    email.subject = subject
    email.body = body
    email.sender = sender
    email.recipient = "me@example.com"
    email.received_at = datetime.now(timezone.utc)
    email.classification = classification
    email.confidence = confidence
    email.status = status
    email.draft_response = draft_response
    email.agent_logs = []
    email.created_at = datetime.now(timezone.utc)
    email.updated_at = datetime.now(timezone.utc)
    return email


def make_agent_log(
    *,
    email_id: uuid.UUID | None = None,
    trace_id: uuid.UUID | None = None,
    step_name: str = "classify",
    step_order: int = 0,
    latency_ms: float = 100.0,
    error_message: str | None = None,
    input_state: dict | None = None,
    output_state: dict | None = None,
) -> AgentLog:
    log = AgentLog.__new__(AgentLog)
    log.id = uuid.uuid4()
    log.email_id = email_id or uuid.uuid4()
    log.trace_id = trace_id or uuid.uuid4()
    log.step_name = step_name
    log.step_order = step_order
    log.latency_ms = latency_ms
    log.error_message = error_message
    log.input_state = input_state
    log.output_state = output_state
    log.tool_executions = []
    log.created_at = datetime.now(timezone.utc)
    log.updated_at = datetime.now(timezone.utc)
    return log


def make_tool_execution(
    *,
    agent_log_id: uuid.UUID | None = None,
    tool_name: str = "search",
    success: bool = True,
    latency_ms: float = 50.0,
    error_message: str | None = None,
) -> ToolExecution:
    te = ToolExecution.__new__(ToolExecution)
    te.id = uuid.uuid4()
    te.agent_log_id = agent_log_id or uuid.uuid4()
    te.tool_name = tool_name
    te.params = {"query": "test"}
    te.result = {"hits": []}
    te.success = success
    te.error_message = error_message
    te.latency_ms = latency_ms
    te.created_at = datetime.now(timezone.utc)
    te.updated_at = datetime.now(timezone.utc)
    return te


# ---------------------------------------------------------------------------
# Pytest fixtures exposing factories
# ---------------------------------------------------------------------------


@pytest.fixture
def user_factory():
    return make_user


@pytest.fixture
def email_factory():
    return make_email


@pytest.fixture
def agent_log_factory():
    return make_agent_log


@pytest.fixture
def tool_execution_factory():
    return make_tool_execution
