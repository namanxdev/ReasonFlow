"""Shared pytest fixtures for the ReasonFlow test suite."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agent.state import AgentState


@pytest.fixture
def sample_email() -> dict[str, Any]:
    """A minimal email dict that mirrors the shape used in AgentState."""
    return {
        "id": str(uuid.uuid4()),
        "user_id": str(uuid.uuid4()),
        "gmail_id": "msg-abc123",
        "thread_id": "thread-xyz",
        "subject": "Meeting request for next week",
        "body": "Hi, could we schedule a meeting for next Tuesday at 2pm?",
        "sender": "alice@example.com",
        "recipient": "bob@example.com",
        "received_at": datetime.now(tz=timezone.utc).isoformat(),
    }


@pytest.fixture
def base_state(sample_email: dict[str, Any]) -> AgentState:
    """Minimal AgentState for use as a base in node tests."""
    return AgentState(
        email=sample_email,
        classification="",
        confidence=0.0,
        context=[],
        selected_tools=[],
        tool_results={},
        draft_response="",
        requires_approval=True,
        final_response="",
        error=None,
        steps=[],
        trace_id=str(uuid.uuid4()),
        tool_params={},
        generation_confidence=0.0,
    )


@pytest.fixture
def mock_db() -> MagicMock:
    """Async-compatible SQLAlchemy session mock."""
    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.execute = AsyncMock()
    return db
