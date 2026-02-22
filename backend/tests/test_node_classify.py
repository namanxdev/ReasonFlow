"""Tests for the classify node."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.nodes.classify import VALID_CATEGORIES, classify_node
from app.llm.schemas import IntentResult


def _make_state(
    subject: str = "Hello",
    body: str = "Can we meet?",
    sender: str = "alice@example.com",
    steps: list[dict[str, Any]] | None = None,
    trace_id: str = "trace-001",
) -> dict[str, Any]:
    return {
        "email": {
            "id": "email-001",
            "subject": subject,
            "body": body,
            "sender": sender,
        },
        "steps": steps or [],
        "trace_id": trace_id,
    }


@pytest.mark.asyncio
async def test_classify_node_returns_classification_and_confidence() -> None:
    """classify_node should return a valid classification and confidence."""
    mock_client = MagicMock()
    mock_client.classify_intent = AsyncMock(
        return_value=IntentResult(intent="meeting_request", confidence=0.92, reasoning="meeting")
    )

    with patch("app.agent.nodes.classify.get_gemini_client", return_value=mock_client):
        result = await classify_node(_make_state())

    assert result["classification"] == "meeting_request"
    assert result["confidence"] == pytest.approx(0.92)
    assert result["error"] is None
    assert len(result["steps"]) == 1
    assert result["steps"][0]["step"] == "classify"


@pytest.mark.asyncio
async def test_classify_node_normalises_unknown_category() -> None:
    """An unknown LLM category should be normalised to 'other'."""
    mock_client = MagicMock()
    mock_client.classify_intent = AsyncMock(
        return_value=IntentResult(intent="banana", confidence=0.7, reasoning="odd")
    )

    with patch("app.agent.nodes.classify.get_gemini_client", return_value=mock_client):
        result = await classify_node(_make_state())

    assert result["classification"] == "other"
    assert result["error"] is None


@pytest.mark.asyncio
async def test_classify_node_clamps_confidence_out_of_range() -> None:
    """Confidence values outside [0, 1] should be clamped."""
    mock_client = MagicMock()
    mock_client.classify_intent = AsyncMock(
        return_value=SimpleNamespace(intent="inquiry", confidence=1.5, reasoning="test")
    )

    with patch("app.agent.nodes.classify.get_gemini_client", return_value=mock_client):
        result = await classify_node(_make_state())

    assert result["confidence"] <= 1.0
    assert result["confidence"] >= 0.0


@pytest.mark.asyncio
async def test_classify_node_handles_llm_error() -> None:
    """classify_node should return safe defaults and an error message on failure."""
    mock_client = MagicMock()
    mock_client.classify_intent = AsyncMock(side_effect=RuntimeError("API unavailable"))

    with patch("app.agent.nodes.classify.get_gemini_client", return_value=mock_client):
        result = await classify_node(_make_state())

    assert result["classification"] == "other"
    assert result["confidence"] == 0.0
    assert result["error"] is not None
    assert "classify_node failed" in result["error"]


@pytest.mark.asyncio
async def test_classify_node_appends_to_existing_steps() -> None:
    """classify_node should append to the existing steps list, not replace it."""
    existing_steps = [{"step": "prior_step", "latency_ms": 10.0}]
    mock_client = MagicMock()
    mock_client.classify_intent = AsyncMock(
        return_value=IntentResult(intent="spam", confidence=0.99, reasoning="spam")
    )

    with patch("app.agent.nodes.classify.get_gemini_client", return_value=mock_client):
        result = await classify_node(_make_state(steps=existing_steps))

    assert len(result["steps"]) == 2
    assert result["steps"][0]["step"] == "prior_step"
    assert result["steps"][1]["step"] == "classify"


def test_valid_categories_contains_all_expected() -> None:
    """VALID_CATEGORIES should include all six expected intent labels."""
    expected = {"inquiry", "meeting_request", "complaint", "follow_up", "spam", "other"}
    assert VALID_CATEGORIES == expected
