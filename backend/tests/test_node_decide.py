"""Tests for the decide node."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.nodes.decide import _FALLBACK_TOOLS, decide_node
from app.llm.schemas import DecisionResult


def _make_state(
    classification: str = "inquiry",
    context: list[str] | None = None,
    trace_id: str = "trace-003",
) -> dict[str, Any]:
    return {
        "email": {
            "id": "email-003",
            "subject": "Product question",
            "body": "I want to know more about pricing.",
            "sender": "bob@example.com",
        },
        "classification": classification,
        "context": context or [],
        "steps": [],
        "trace_id": trace_id,
    }


@pytest.mark.asyncio
async def test_decide_node_spam_short_circuits() -> None:
    """Spam emails should immediately return an empty selected_tools list."""
    result = await decide_node(_make_state(classification="spam"))

    assert result["selected_tools"] == []
    assert result["tool_params"] == {}
    assert len(result["steps"]) == 1
    assert result["steps"][0]["step"] == "decide"


@pytest.mark.asyncio
async def test_decide_node_uses_llm_result() -> None:
    """decide_node should honour the tools returned by the LLM."""
    mock_client = MagicMock()
    mock_client.decide_tools = AsyncMock(
        return_value=DecisionResult(
            selected_tools=["get_contact", "create_draft"],
            reasoning="Need CRM data and a draft",
            params={"get_contact": {"email": "bob@example.com"}},
        )
    )

    with patch("app.agent.nodes.decide.get_gemini_client", return_value=mock_client):
        result = await decide_node(_make_state(classification="inquiry"))

    assert result["selected_tools"] == ["get_contact", "create_draft"]
    assert result["tool_params"] == {"get_contact": {"email": "bob@example.com"}}
    assert result["error"] is None


@pytest.mark.asyncio
async def test_decide_node_falls_back_on_llm_error() -> None:
    """When the LLM call fails, decide_node should use the deterministic fallback."""
    mock_client = MagicMock()
    mock_client.decide_tools = AsyncMock(side_effect=RuntimeError("LLM timeout"))

    with patch("app.agent.nodes.decide.get_gemini_client", return_value=mock_client):
        result = await decide_node(_make_state(classification="complaint"))

    expected_fallback = _FALLBACK_TOOLS["complaint"]
    assert result["selected_tools"] == expected_fallback
    assert result["error"] is not None
    assert "fallback" in result["steps"][0]


@pytest.mark.asyncio
async def test_decide_node_fallback_meeting_request() -> None:
    """Fallback for meeting_request should include calendar tools."""
    mock_client = MagicMock()
    mock_client.decide_tools = AsyncMock(side_effect=RuntimeError("timeout"))

    with patch("app.agent.nodes.decide.get_gemini_client", return_value=mock_client):
        result = await decide_node(_make_state(classification="meeting_request"))

    assert "check_calendar" in result["selected_tools"]
    assert "create_draft" in result["selected_tools"]


@pytest.mark.asyncio
async def test_decide_node_fallback_for_unknown_classification() -> None:
    """Fallback for unknown classification defaults to ['create_draft']."""
    mock_client = MagicMock()
    mock_client.decide_tools = AsyncMock(side_effect=RuntimeError("fail"))

    with patch("app.agent.nodes.decide.get_gemini_client", return_value=mock_client):
        result = await decide_node(_make_state(classification="unknown_xyz"))

    assert result["selected_tools"] == ["create_draft"]


@pytest.mark.asyncio
async def test_decide_node_appends_step() -> None:
    """decide_node must append exactly one entry to steps."""
    mock_client = MagicMock()
    mock_client.decide_tools = AsyncMock(
        return_value=DecisionResult(selected_tools=[], reasoning="", params={})
    )

    with patch("app.agent.nodes.decide.get_gemini_client", return_value=mock_client):
        result = await decide_node(_make_state(classification="follow_up"))

    assert len(result["steps"]) == 1
    assert result["steps"][0]["step"] == "decide"


def test_fallback_tools_covers_all_categories() -> None:
    """Every expected classification category should have a fallback entry."""
    expected_keys = {"meeting_request", "complaint", "inquiry", "follow_up", "spam", "other"}
    assert expected_keys == set(_FALLBACK_TOOLS.keys())
