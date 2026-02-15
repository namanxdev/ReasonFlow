"""Tests for the review node."""

from __future__ import annotations

from typing import Any

import pytest

from app.agent.nodes.review import AUTO_APPROVE_THRESHOLD, review_node


def _make_state(
    classification: str = "inquiry",
    confidence: float = 0.9,
    draft_response: str = "This is the draft.",
    trace_id: str = "trace-006",
) -> dict[str, Any]:
    return {
        "classification": classification,
        "confidence": confidence,
        "draft_response": draft_response,
        "steps": [],
        "trace_id": trace_id,
    }


@pytest.mark.asyncio
async def test_review_node_auto_approves_high_confidence_non_complaint() -> None:
    """High confidence, non-complaint email should be auto-approved."""
    result = await review_node(_make_state(classification="inquiry", confidence=0.95))

    assert result["requires_approval"] is False
    assert result["final_response"] == "This is the draft."
    assert len(result["steps"]) == 1


@pytest.mark.asyncio
async def test_review_node_requires_approval_for_complaint() -> None:
    """Complaints should always require human approval regardless of confidence."""
    result = await review_node(
        _make_state(classification="complaint", confidence=0.99)
    )

    assert result["requires_approval"] is True
    assert result["final_response"] == ""


@pytest.mark.asyncio
async def test_review_node_requires_approval_for_low_confidence() -> None:
    """Confidence below the threshold should trigger human review."""
    result = await review_node(
        _make_state(classification="inquiry", confidence=AUTO_APPROVE_THRESHOLD - 0.01)
    )

    assert result["requires_approval"] is True
    assert result["final_response"] == ""


@pytest.mark.asyncio
async def test_review_node_at_exact_threshold_auto_approves() -> None:
    """Confidence exactly at AUTO_APPROVE_THRESHOLD should be auto-approved."""
    result = await review_node(
        _make_state(classification="inquiry", confidence=AUTO_APPROVE_THRESHOLD)
    )

    assert result["requires_approval"] is False
    assert result["final_response"] != ""


@pytest.mark.asyncio
async def test_review_node_sets_final_response_only_when_approved() -> None:
    """final_response should be empty string when approval is required."""
    approved = await review_node(
        _make_state(classification="follow_up", confidence=0.85)
    )
    needs_review = await review_node(
        _make_state(classification="follow_up", confidence=0.5)
    )

    assert approved["final_response"] == "This is the draft."
    assert needs_review["final_response"] == ""


@pytest.mark.asyncio
async def test_review_node_appends_step_with_reasoning() -> None:
    """The step trace entry should include the reasoning string."""
    result = await review_node(_make_state(confidence=0.95))

    step = result["steps"][0]
    assert step["step"] == "review"
    assert "reasoning" in step
    assert isinstance(step["reasoning"], str)


@pytest.mark.asyncio
async def test_review_node_meeting_request_auto_approves_with_high_confidence() -> None:
    """meeting_request with high confidence should be auto-approved."""
    result = await review_node(
        _make_state(classification="meeting_request", confidence=0.92)
    )

    assert result["requires_approval"] is False


@pytest.mark.asyncio
async def test_review_node_meeting_request_requires_review_with_low_confidence() -> None:
    """meeting_request with low confidence should require approval."""
    result = await review_node(
        _make_state(classification="meeting_request", confidence=0.6)
    )

    assert result["requires_approval"] is True
