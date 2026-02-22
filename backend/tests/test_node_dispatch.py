"""Tests for the dispatch node."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.nodes.dispatch import dispatch_node


def _make_state(
    requires_approval: bool = False,
    final_response: str = "Approved response.",
    draft_response: str = "Draft response.",
    trace_id: str = "trace-007",
) -> dict[str, Any]:
    return {
        "email": {
            "id": "d50f5b52-1111-1111-1111-000000000001",
            "user_id": "d50f5b52-2222-2222-2222-000000000001",
            "subject": "Hello",
            "body": "World",
            "sender": "alice@example.com",
            "thread_id": "thread-001",
        },
        "requires_approval": requires_approval,
        "final_response": final_response,
        "draft_response": draft_response,
        "steps": [],
        "trace_id": trace_id,
    }


@pytest.mark.asyncio
async def test_dispatch_node_sends_email_when_auto_approved() -> None:
    """dispatch_node should call GmailClient.send_email for auto-approved emails."""
    mock_gmail = MagicMock()
    mock_gmail.send_email = AsyncMock(return_value={"id": "msg-001"})
    mock_module = MagicMock()
    mock_module.GmailClient = MagicMock(return_value=mock_gmail)

    fake_creds = {"access_token": "fake-token"}
    with (
        patch.dict("sys.modules", {"app.integrations.gmail.client": mock_module}),
        patch("app.agent.nodes.dispatch._get_user_credentials", AsyncMock(return_value=fake_creds)),
    ):
        result = await dispatch_node(_make_state(requires_approval=False), db=None)

    mock_gmail.send_email.assert_awaited_once()
    step = result["steps"][0]
    assert step["action"] in ("sent", "send_pending")


@pytest.mark.asyncio
async def test_dispatch_node_creates_draft_when_approval_required() -> None:
    """dispatch_node should call GmailClient.create_draft for review-needed emails."""
    mock_gmail = MagicMock()
    mock_gmail.create_draft = AsyncMock(return_value={"id": "draft-001"})
    mock_module = MagicMock()
    mock_module.GmailClient = MagicMock(return_value=mock_gmail)

    fake_creds = {"access_token": "fake-token"}
    with (
        patch.dict("sys.modules", {"app.integrations.gmail.client": mock_module}),
        patch("app.agent.nodes.dispatch._get_user_credentials", AsyncMock(return_value=fake_creds)),
    ):
        result = await dispatch_node(_make_state(requires_approval=True), db=None)

    mock_gmail.create_draft.assert_awaited_once()
    step = result["steps"][0]
    assert step["action"] in ("draft_created", "draft_pending")


@pytest.mark.asyncio
async def test_dispatch_node_handles_missing_gmail_client_gracefully() -> None:
    """dispatch_node should not raise when GmailClient is unavailable."""
    with patch.dict("sys.modules", {"app.integrations.gmail.client": None}):
        result = await dispatch_node(_make_state(requires_approval=False), db=None)

    # Should record that the action is pending, not raise.
    step = result["steps"][0]
    assert step.get("action") is not None


@pytest.mark.asyncio
async def test_dispatch_node_appends_step() -> None:
    """dispatch_node should append exactly one step entry."""
    with patch.dict("sys.modules", {"app.integrations.gmail.client": None}):
        result = await dispatch_node(_make_state(), db=None)

    assert len(result["steps"]) == 1
    assert result["steps"][0]["step"] == "dispatch"


@pytest.mark.asyncio
async def test_dispatch_node_records_requires_approval_in_step() -> None:
    """The step entry should reflect the requires_approval flag."""
    with patch.dict("sys.modules", {"app.integrations.gmail.client": None}):
        result_approved = await dispatch_node(_make_state(requires_approval=False), db=None)
        result_review = await dispatch_node(_make_state(requires_approval=True), db=None)

    assert result_approved["steps"][0]["requires_approval"] is False
    assert result_review["steps"][0]["requires_approval"] is True


@pytest.mark.asyncio
async def test_dispatch_node_sets_error_on_send_failure() -> None:
    """dispatch_node should set error when Gmail send raises an exception."""
    mock_gmail = MagicMock()
    mock_gmail.send_email = AsyncMock(side_effect=RuntimeError("Gmail API down"))
    mock_module = MagicMock()
    mock_module.GmailClient = MagicMock(return_value=mock_gmail)

    with patch.dict("sys.modules", {"app.integrations.gmail.client": mock_module}):
        result = await dispatch_node(_make_state(requires_approval=False), db=None)

    assert result["error"] is not None
    assert "send failed" in result["error"]
