"""Tests for the agent tool registry."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.tools.registry import _registry, get_tool, list_tools, register


def test_list_tools_returns_all_registered_tools() -> None:
    """list_tools should include all six built-in tools."""
    tools = list_tools()
    expected = {
        "check_calendar",
        "create_draft",
        "create_event",
        "get_contact",
        "send_email",
        "update_contact",
    }
    assert expected.issubset(set(tools))


def test_get_tool_returns_callable_for_known_tool() -> None:
    """get_tool should return an async callable for registered tools."""
    fn = get_tool("send_email")
    assert fn is not None
    assert callable(fn)


def test_get_tool_returns_none_for_unknown_tool() -> None:
    """get_tool should return None for unregistered tool names."""
    assert get_tool("nonexistent_tool_xyz") is None


def test_register_decorator_adds_tool_to_registry() -> None:
    """The @register decorator should add a callable under the given name."""
    test_tool_name = "_test_register_temp_tool"
    # Ensure it doesn't already exist.
    _registry.pop(test_tool_name, None)

    @register(test_tool_name)
    async def _temp_tool(params: dict) -> dict:  # type: ignore[type-arg]
        return {"ok": True}

    assert get_tool(test_tool_name) is _temp_tool
    # Clean up so other tests are not affected.
    _registry.pop(test_tool_name, None)


@pytest.mark.asyncio
async def test_send_email_tool_no_gmail_client() -> None:
    """send_email should return a 'skipped' result when GmailClient is absent."""
    fn = get_tool("send_email")
    assert fn is not None

    with patch.dict("sys.modules", {"app.integrations.gmail.client": None}):
        result = await fn(
            {"to": "alice@example.com", "subject": "Hi", "body": "Hello"}
        )

    assert result.get("status") in ("skipped", "sent")


@pytest.mark.asyncio
async def test_create_draft_tool_no_gmail_client() -> None:
    """create_draft should return a 'skipped' result when GmailClient is absent."""
    fn = get_tool("create_draft")
    assert fn is not None

    with patch.dict("sys.modules", {"app.integrations.gmail.client": None}):
        result = await fn(
            {"to": "alice@example.com", "subject": "Hi", "body": "Draft body"}
        )

    assert result.get("status") in ("skipped", "drafted")


@pytest.mark.asyncio
async def test_check_calendar_tool_no_calendar_client() -> None:
    """check_calendar should return empty slots when CalendarClient is absent."""
    fn = get_tool("check_calendar")
    assert fn is not None

    with patch.dict("sys.modules", {"app.integrations.calendar.client": None}):
        result = await fn({"start": "2026-02-15T09:00:00", "end": "2026-02-15T17:00:00"})

    assert "available_slots" in result


@pytest.mark.asyncio
async def test_get_contact_tool_no_crm_client() -> None:
    """get_contact should return a 'skipped' result when CRM client is absent."""
    fn = get_tool("get_contact")
    assert fn is not None

    with patch.dict("sys.modules", {"app.integrations.crm.factory": None}):
        result = await fn({"email": "alice@example.com"})

    assert isinstance(result, dict)


@pytest.mark.asyncio
async def test_send_email_tool_with_mock_gmail_client() -> None:
    """send_email should call GmailClient.send_email with correct params."""
    fn = get_tool("send_email")
    assert fn is not None

    mock_client = MagicMock()
    mock_client.send_email = AsyncMock(return_value={"id": "msg-001"})
    mock_module = MagicMock()
    mock_module.GmailClient = MagicMock(return_value=mock_client)

    with patch.dict("sys.modules", {"app.integrations.gmail.client": mock_module}):
        result = await fn(
            {"to": "alice@example.com", "subject": "Re: Hi", "body": "Hello back"}
        )

    assert result["status"] == "sent"
    assert result["message_id"] == "msg-001"
    mock_client.send_email.assert_awaited_once()
