"""Tests for AgentState TypedDict definition."""

from __future__ import annotations

import uuid
from typing import Any

from app.agent.state import AgentState


def test_agent_state_can_be_constructed_with_all_fields() -> None:
    """AgentState accepts all defined fields without raising."""
    state: AgentState = {
        "email": {"id": str(uuid.uuid4()), "subject": "Test", "body": "Hello"},
        "classification": "inquiry",
        "confidence": 0.95,
        "context": ["context line 1", "context line 2"],
        "selected_tools": ["get_contact", "create_draft"],
        "tool_results": {"get_contact": {"name": "Alice"}},
        "draft_response": "Thank you for reaching out.",
        "requires_approval": False,
        "final_response": "Thank you for reaching out.",
        "error": None,
        "steps": [{"step": "classify", "latency_ms": 123.4}],
        "trace_id": str(uuid.uuid4()),
        "tool_params": {"get_contact": {"email": "alice@example.com"}},
        "generation_confidence": 0.88,
    }
    assert state["classification"] == "inquiry"
    assert state["confidence"] == 0.95
    assert state["requires_approval"] is False


def test_agent_state_partial_construction() -> None:
    """AgentState allows partial construction because total=False."""
    state: AgentState = {"email": {"id": "x"}}  # type: ignore[typeddict-item]
    assert state["email"]["id"] == "x"


def test_agent_state_steps_is_list_of_dicts() -> None:
    """Steps field should hold a list of dicts."""
    steps: list[dict[str, Any]] = [
        {"step": "classify", "latency_ms": 50.0},
        {"step": "retrieve", "latency_ms": 120.0},
    ]
    state: AgentState = {"steps": steps}  # type: ignore[typeddict-item]
    assert len(state["steps"]) == 2
    assert state["steps"][0]["step"] == "classify"


def test_agent_state_error_is_optional() -> None:
    """The error field can be None or a string."""
    state_no_error: AgentState = {"error": None}  # type: ignore[typeddict-item]
    state_with_error: AgentState = {"error": "something went wrong"}  # type: ignore[typeddict-item]
    assert state_no_error["error"] is None
    assert isinstance(state_with_error["error"], str)
