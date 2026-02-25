"""Tests for the retrieve node."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.nodes.retrieve import retrieve_node


def _make_state(
    classification: str = "inquiry",
    sender: str = "alice@example.com",
    trace_id: str = "trace-002",
) -> dict[str, Any]:
    return {
        "email": {
            "id": "email-002",
            "subject": "Quick question",
            "body": "I had a question about your product.",
            "sender": sender,
            "user_id": "user-001",
        },
        "classification": classification,
        "steps": [],
        "trace_id": trace_id,
    }


@pytest.mark.asyncio
async def test_retrieve_node_returns_context_list() -> None:
    """retrieve_node should always return a list in the 'context' key."""
    with (
        patch.dict("sys.modules", {"app.retrieval": None}),
        patch.dict("sys.modules", {"app.integrations.crm.factory": None}),
        patch.dict("sys.modules", {"app.integrations.calendar.client": None}),
    ):
        result = await retrieve_node(_make_state())

    assert "context" in result
    assert isinstance(result["context"], list)


@pytest.mark.asyncio
async def test_retrieve_node_appends_step() -> None:
    """retrieve_node should append one entry to steps."""
    with (
        patch.dict("sys.modules", {"app.retrieval": None}),
        patch.dict("sys.modules", {"app.integrations.crm.factory": None}),
        patch.dict("sys.modules", {"app.integrations.calendar.client": None}),
    ):
        result = await retrieve_node(_make_state())

    assert len(result["steps"]) == 1
    assert result["steps"][0]["step"] == "retrieve"


@pytest.mark.asyncio
async def test_retrieve_node_incorporates_vector_search_results() -> None:
    """When the retrieval module is available, results are added to context."""
    mock_retrieval = MagicMock()
    mock_retrieval.search_similar = AsyncMock(
        return_value=["Past email: we discussed pricing.", "Past email: follow-up on demo."]
    )

    with patch.dict("sys.modules", {"app.retrieval": mock_retrieval}):
        with (
            patch.dict("sys.modules", {"app.integrations.crm.factory": None}),
            patch.dict("sys.modules", {"app.integrations.calendar.client": None}),
        ):
            result = await retrieve_node(_make_state())

    assert any("Past email" in c for c in result["context"])


@pytest.mark.asyncio
async def test_retrieve_node_incorporates_crm_contact() -> None:
    """CRM contact data should appear in context when the client is available."""
    mock_crm_client = MagicMock()
    mock_crm_client.get_contact = AsyncMock(
        return_value={"name": "Alice Smith", "company": "Acme Corp", "notes": "VIP"}
    )
    mock_crm_factory = MagicMock()
    mock_crm_factory.get_crm_client = MagicMock(return_value=mock_crm_client)

    with (
        patch.dict("sys.modules", {"app.retrieval": None}),
        patch.dict("sys.modules", {"app.integrations.crm.factory": mock_crm_factory}),
        patch.dict("sys.modules", {"app.integrations.calendar.client": None}),
    ):
        result = await retrieve_node(_make_state())

    assert any("Alice Smith" in c for c in result["context"])


@pytest.mark.asyncio
async def test_retrieve_node_skips_calendar_for_non_meeting() -> None:
    """Calendar lookup should be skipped for non-meeting classifications."""
    mock_cal_client = MagicMock()
    mock_cal_client.get_upcoming_events = AsyncMock(
        return_value=[{
            "title": "Stand-up",
            "start": "2026-02-15T09:00:00",
            "end": "2026-02-15T09:30:00",
        }]
    )
    mock_cal_module = MagicMock()
    mock_cal_module.CalendarClient = MagicMock(return_value=mock_cal_client)

    with (
        patch.dict("sys.modules", {"app.retrieval": None}),
        patch.dict("sys.modules", {"app.integrations.crm.factory": None}),
        patch.dict("sys.modules", {"app.integrations.calendar.client": mock_cal_module}),
    ):
        result = await retrieve_node(_make_state(classification="inquiry"))

    # Calendar events should NOT appear for inquiry classification.
    assert not any("calendar" in c.lower() for c in result["context"])
    # CalendarClient.get_upcoming_events should not have been called.
    mock_cal_client.get_upcoming_events.assert_not_awaited()


@pytest.mark.asyncio
async def test_retrieve_node_fetches_calendar_for_meeting_request() -> None:
    """Calendar events should be fetched for meeting_request classification."""
    mock_cal_client = MagicMock()
    mock_cal_client.get_upcoming_events = AsyncMock(
        return_value=[
            {"title": "All-Hands", "start": "2026-02-16T14:00:00", "end": "2026-02-16T15:00:00"}
        ]
    )
    mock_cal_module = MagicMock()
    mock_cal_module.CalendarClient = MagicMock(return_value=mock_cal_client)

    with (
        patch.dict("sys.modules", {"app.retrieval": None}),
        patch.dict("sys.modules", {"app.integrations.crm.factory": None}),
        patch.dict("sys.modules", {"app.integrations.calendar.client": mock_cal_module}),
    ):
        result = await retrieve_node(_make_state(classification="meeting_request"))

    assert any("All-Hands" in c for c in result["context"])


@pytest.mark.asyncio
async def test_retrieve_node_handles_all_sources_failing() -> None:
    """retrieve_node should succeed with an empty context when all sources fail."""
    mock_retrieval = MagicMock()
    mock_retrieval.search_similar = AsyncMock(side_effect=RuntimeError("search down"))

    with patch.dict("sys.modules", {"app.retrieval": mock_retrieval}):
        with (
            patch.dict("sys.modules", {"app.integrations.crm.factory": None}),
            patch.dict("sys.modules", {"app.integrations.calendar.client": None}),
        ):
            result = await retrieve_node(_make_state())

    # Should not raise; should return an empty context list.
    assert isinstance(result["context"], list)
