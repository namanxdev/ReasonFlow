"""Tests for the execute node."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.nodes.execute import execute_node
from app.agent.tools.registry import _registry


def _make_state(
    selected_tools: list[str] | None = None,
    tool_params: dict[str, dict[str, Any]] | None = None,
    trace_id: str = "trace-004",
) -> dict[str, Any]:
    return {
        "email": {
            "id": "d50f5b52-0000-0000-0000-000000000001",
            "subject": "Test",
            "body": "Body",
            "sender": "alice@example.com",
            "thread_id": "thread-001",
        },
        "selected_tools": selected_tools or [],
        "tool_params": tool_params or {},
        "steps": [],
        "trace_id": trace_id,
    }


@pytest.mark.asyncio
async def test_execute_node_no_tools_returns_empty_results() -> None:
    """With no selected tools, tool_results should be an empty dict."""
    result = await execute_node(_make_state(selected_tools=[]))

    assert result["tool_results"] == {}
    assert len(result["steps"]) == 1
    assert result["steps"][0]["step"] == "execute"


@pytest.mark.asyncio
async def test_execute_node_runs_registered_tool() -> None:
    """execute_node should call a registered tool and collect the result."""
    async def _mock_tool(params: dict) -> dict:  # type: ignore[type-arg]
        return {"status": "ok", "data": "test"}

    _registry["_test_exec_tool"] = _mock_tool

    try:
        result = await execute_node(_make_state(selected_tools=["_test_exec_tool"]))

        assert "_test_exec_tool" in result["tool_results"]
        assert result["tool_results"]["_test_exec_tool"]["status"] == "ok"
    finally:
        _registry.pop("_test_exec_tool", None)


@pytest.mark.asyncio
async def test_execute_node_handles_unknown_tool_gracefully() -> None:
    """An unregistered tool should produce an error result without raising."""
    result = await execute_node(_make_state(selected_tools=["totally_unknown_tool"]))

    assert "totally_unknown_tool" in result["tool_results"]
    assert "error" in result["tool_results"]["totally_unknown_tool"]
    # The node itself should not set a global error if only one tool fails
    # and the failure is "not registered" (a configuration issue, not a runtime crash).


@pytest.mark.asyncio
async def test_execute_node_isolates_tool_failure() -> None:
    """A failing tool should not stop subsequent tools from running."""
    async def _failing_tool(params: dict) -> dict:  # type: ignore[type-arg]
        raise RuntimeError("tool crashed")

    async def _succeeding_tool(params: dict) -> dict:  # type: ignore[type-arg]
        return {"result": "success"}

    _registry["_fail_tool"] = _failing_tool
    _registry["_ok_tool"] = _succeeding_tool

    try:
        result = await execute_node(
            _make_state(selected_tools=["_fail_tool", "_ok_tool"])
        )

        assert "error" in result["tool_results"]["_fail_tool"]
        assert result["tool_results"]["_ok_tool"]["result"] == "success"
    finally:
        _registry.pop("_fail_tool", None)
        _registry.pop("_ok_tool", None)


@pytest.mark.asyncio
async def test_execute_node_records_step_summary() -> None:
    """execute_node should record a step entry with a 'tools' summary list."""
    async def _noop_tool(params: dict) -> dict:  # type: ignore[type-arg]
        return {"done": True}

    _registry["_noop_tool"] = _noop_tool

    try:
        result = await execute_node(_make_state(selected_tools=["_noop_tool"]))
        step = result["steps"][0]
        assert step["step"] == "execute"
        assert isinstance(step["tools"], list)
        assert step["tools"][0]["tool"] == "_noop_tool"
        assert step["tools"][0]["success"] is True
    finally:
        _registry.pop("_noop_tool", None)


@pytest.mark.asyncio
async def test_execute_node_merges_tool_params() -> None:
    """Tool params from the decision node should be passed to the tool."""
    received_params: dict[str, Any] = {}

    async def _capturing_tool(params: dict) -> dict:  # type: ignore[type-arg]
        received_params.update(params)
        return {"captured": True}

    _registry["_cap_tool"] = _capturing_tool

    try:
        state = _make_state(
            selected_tools=["_cap_tool"],
            tool_params={"_cap_tool": {"custom_key": "custom_value"}},
        )
        await execute_node(state)

        assert received_params.get("custom_key") == "custom_value"
        # Default email fields should also be present.
        assert "sender" in received_params
    finally:
        _registry.pop("_cap_tool", None)


@pytest.mark.asyncio
async def test_execute_node_without_db_skips_persistence() -> None:
    """execute_node should work correctly when no db session is provided."""
    async def _simple_tool(params: dict) -> dict:  # type: ignore[type-arg]
        return {"ok": True}

    _registry["_simple_tool"] = _simple_tool

    try:
        result = await execute_node(_make_state(selected_tools=["_simple_tool"]), db=None)
        assert result["tool_results"]["_simple_tool"]["ok"] is True
    finally:
        _registry.pop("_simple_tool", None)
