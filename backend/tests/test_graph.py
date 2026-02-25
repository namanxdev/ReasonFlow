"""Tests for the LangGraph graph routing logic and conditional edges."""

from __future__ import annotations

from typing import Any

from langgraph.graph import END

from app.agent.graph import _route_after_classify, _route_after_decide, _route_after_review
from app.agent.state import AgentState


def _state(**kwargs: Any) -> AgentState:
    base: AgentState = {
        "email": {},
        "classification": "inquiry",
        "confidence": 0.9,
        "context": [],
        "selected_tools": [],
        "tool_results": {},
        "draft_response": "",
        "requires_approval": False,
        "final_response": "",
        "error": None,
        "steps": [],
        "trace_id": "trace-graph-001",
        "tool_params": {},
        "generation_confidence": 0.0,
    }
    base.update(kwargs)  # type: ignore[typeddict-item]
    return base


# ---------------------------------------------------------------------------
# _route_after_classify
# ---------------------------------------------------------------------------


def test_route_classify_spam_high_confidence_goes_to_end() -> None:
    """High-confidence spam should short-circuit directly to END."""
    state = _state(classification="spam", confidence=0.95)
    route = _route_after_classify(state)
    assert route == END


def test_route_classify_spam_low_confidence_continues() -> None:
    """Low-confidence spam should still go through retrieve (not short-circuit)."""
    state = _state(classification="spam", confidence=0.5)
    route = _route_after_classify(state)
    assert route == "retrieve"


def test_route_classify_spam_exactly_at_threshold_goes_to_end() -> None:
    """Confidence exactly at 0.8 for spam should short-circuit."""
    state = _state(classification="spam", confidence=0.8)
    route = _route_after_classify(state)
    assert route == END


def test_route_classify_non_spam_always_continues() -> None:
    """Non-spam classifications should always route to retrieve."""
    for classification in ("inquiry", "meeting_request", "complaint", "follow_up", "other"):
        state = _state(classification=classification, confidence=0.99)
        route = _route_after_classify(state)
        assert route == "retrieve", f"Expected 'retrieve' for {classification}"


# ---------------------------------------------------------------------------
# _route_after_decide
# ---------------------------------------------------------------------------


def test_route_decide_with_tools_goes_to_execute() -> None:
    """When tools are selected, route to execute."""
    state = _state(selected_tools=["get_contact", "create_draft"])
    assert _route_after_decide(state) == "execute"


def test_route_decide_without_tools_goes_to_generate() -> None:
    """When no tools are selected, skip execute and go directly to generate."""
    state = _state(selected_tools=[])
    assert _route_after_decide(state) == "generate"


# ---------------------------------------------------------------------------
# _route_after_review
# ---------------------------------------------------------------------------


def test_route_review_auto_approved_goes_to_dispatch() -> None:
    """Auto-approved emails should route to dispatch."""
    state = _state(requires_approval=False)
    assert _route_after_review(state) == "dispatch"


def test_route_review_needs_approval_goes_to_human_queue() -> None:
    """Emails requiring approval should route to human_queue."""
    state = _state(requires_approval=True)
    assert _route_after_review(state) == "human_queue"


def test_route_review_defaults_to_human_queue_when_flag_absent() -> None:
    """When requires_approval key is missing, default to human_queue (safe)."""
    state: AgentState = {}  # type: ignore[typeddict-item]
    assert _route_after_review(state) == "human_queue"
