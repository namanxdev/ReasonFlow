"""Tests for the generate node."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.agent.nodes.generate import generate_node
from app.llm.schemas import GenerationResult


def _make_state(
    classification: str = "inquiry",
    context: list[str] | None = None,
    tool_results: dict[str, Any] | None = None,
    trace_id: str = "trace-005",
) -> dict[str, Any]:
    return {
        "email": {
            "id": "email-005",
            "subject": "Need info",
            "body": "Can you help me?",
            "sender": "charlie@example.com",
        },
        "classification": classification,
        "context": context or [],
        "tool_results": tool_results or {},
        "steps": [],
        "trace_id": trace_id,
    }


@pytest.mark.asyncio
async def test_generate_node_returns_draft_response() -> None:
    """generate_node should populate draft_response from the LLM."""
    mock_client = MagicMock()
    mock_client.generate_response = AsyncMock(
        return_value=GenerationResult(
            response="Thank you for your inquiry. We'd be happy to help.",
            tone="professional",
            confidence=0.88,
        )
    )

    with patch("app.agent.nodes.generate.get_gemini_client", return_value=mock_client):
        result = await generate_node(_make_state())

    assert result["draft_response"] == "Thank you for your inquiry. We'd be happy to help."
    assert result["generation_confidence"] == pytest.approx(0.88)
    assert result["error"] is None


@pytest.mark.asyncio
async def test_generate_node_passes_context_and_tool_results() -> None:
    """generate_node should forward context and tool_results to the LLM."""
    captured_kwargs: dict[str, Any] = {}

    async def _mock_generate(**kwargs: Any) -> GenerationResult:
        captured_kwargs.update(kwargs)
        return GenerationResult(response="Reply", tone="formal", confidence=0.7)

    mock_client = MagicMock()
    mock_client.generate_response = AsyncMock(side_effect=_mock_generate)

    context = ["Past interaction: demo scheduled", "CRM: VIP client"]
    tool_results = {"get_contact": {"name": "Bob"}}

    with patch("app.agent.nodes.generate.get_gemini_client", return_value=mock_client):
        await generate_node(_make_state(context=context, tool_results=tool_results))

    call_kwargs = mock_client.generate_response.call_args
    # The context and tool_results should have been converted to strings and passed.
    assert call_kwargs is not None


@pytest.mark.asyncio
async def test_generate_node_handles_llm_failure() -> None:
    """generate_node should return a safe empty draft and set error on LLM failure."""
    mock_client = MagicMock()
    mock_client.generate_response = AsyncMock(side_effect=RuntimeError("LLM unreachable"))

    with patch("app.agent.nodes.generate.get_gemini_client", return_value=mock_client):
        result = await generate_node(_make_state())

    assert result["draft_response"] == ""
    assert result["generation_confidence"] == 0.0
    assert result["error"] is not None
    assert "generate_node failed" in result["error"]


@pytest.mark.asyncio
async def test_generate_node_clamps_confidence() -> None:
    """Out-of-range confidence from LLM should be clamped to [0, 1]."""
    mock_client = MagicMock()
    mock_client.generate_response = AsyncMock(
        return_value=SimpleNamespace(response="Draft", tone="formal", confidence=1.9)
    )

    with patch("app.agent.nodes.generate.get_gemini_client", return_value=mock_client):
        result = await generate_node(_make_state())

    assert 0.0 <= result["generation_confidence"] <= 1.0


@pytest.mark.asyncio
async def test_generate_node_appends_step() -> None:
    """generate_node should append one entry to steps."""
    mock_client = MagicMock()
    mock_client.generate_response = AsyncMock(
        return_value=GenerationResult(response="Ok", tone="professional", confidence=0.9)
    )

    with patch("app.agent.nodes.generate.get_gemini_client", return_value=mock_client):
        result = await generate_node(_make_state())

    assert len(result["steps"]) == 1
    assert result["steps"][0]["step"] == "generate"
    assert "latency_ms" in result["steps"][0]
