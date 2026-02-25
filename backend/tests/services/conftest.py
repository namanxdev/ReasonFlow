"""Fixtures shared across service unit tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.email import EmailClassification, EmailStatus

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
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        email=email,
        hashed_password=hashed_password,
        oauth_token_encrypted=oauth_token_encrypted,
        oauth_refresh_token_encrypted=oauth_refresh_token_encrypted,
        emails=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


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
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        user_id=user_id or uuid.uuid4(),
        gmail_id=gmail_id,
        thread_id="thread-1",
        subject=subject,
        body=body,
        sender=sender,
        recipient="me@example.com",
        received_at=datetime.now(UTC),
        classification=classification,
        confidence=confidence,
        status=status,
        draft_response=draft_response,
        agent_logs=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


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
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        email_id=email_id or uuid.uuid4(),
        trace_id=trace_id or uuid.uuid4(),
        step_name=step_name,
        step_order=step_order,
        latency_ms=latency_ms,
        error_message=error_message,
        input_state=input_state,
        output_state=output_state,
        tool_executions=[],
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def make_tool_execution(
    *,
    agent_log_id: uuid.UUID | None = None,
    tool_name: str = "search",
    success: bool = True,
    latency_ms: float = 50.0,
    error_message: str | None = None,
) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid.uuid4(),
        agent_log_id=agent_log_id or uuid.uuid4(),
        tool_name=tool_name,
        params={"query": "test"},
        result={"hits": []},
        success=success,
        error_message=error_message,
        latency_ms=latency_ms,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


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
