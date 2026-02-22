"""Response generation node — uses LLM to draft an email reply."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.agent.state import AgentState
from app.llm.client import get_gemini_client
from app.llm.utils import truncate_text

logger = logging.getLogger(__name__)


async def generate_node(state: AgentState) -> dict[str, Any]:
    """Generate a draft email response.

    Calls ``GeminiClient.generate_response`` with the full context: original
    email, classification, retrieved context, and tool results.

    Reads:
        ``email``, ``classification``, ``context``, ``tool_results``

    Writes:
        ``draft_response``       — generated response text.
        ``generation_confidence``— LLM's own confidence in the response.
        ``steps``                — appended step trace entry.
        ``error``                — set on failure.
    """
    step_start = time.monotonic()
    step_name = "generate"
    current_steps: list[dict[str, Any]] = list(state.get("steps", []))

    email: dict[str, Any] = state.get("email", {})
    classification: str = state.get("classification", "other")
    context: list[str] = state.get("context", [])
    tool_results: dict[str, Any] = state.get("tool_results", {})

    logger.info(
        "generate_node: starting — trace_id=%s classification=%s",
        state.get("trace_id", "unknown"),
        classification,
    )

    # Format context and tool results as readable strings for the prompt.
    # Truncate email body to avoid exceeding LLM context window.
    context_text = "\n".join(context) if context else "(no context available)"
    tool_results_text = (
        json.dumps(tool_results, indent=2, default=str) if tool_results else "(no tool results)"
    )
    body = truncate_text(email.get("body", ""), max_chars=4000)

    try:
        client = get_gemini_client()
        result = await client.generate_response(
            subject=email.get("subject", ""),
            body=body,
            sender=email.get("sender", ""),
            classification=classification,
            context=context_text,
            tool_results=tool_results_text,
        )

        draft_response = result.response
        generation_confidence = max(0.0, min(1.0, result.confidence))

        latency_ms = (time.monotonic() - step_start) * 1000
        current_steps.append(
            {
                "step": step_name,
                "tone": result.tone,
                "generation_confidence": generation_confidence,
                "response_length": len(draft_response),
                "latency_ms": latency_ms,
            }
        )

        logger.info(
            "generate_node: done — confidence=%.3f length=%d latency_ms=%.1f",
            generation_confidence,
            len(draft_response),
            latency_ms,
        )

        return {
            "draft_response": draft_response,
            "generation_confidence": generation_confidence,
            "steps": current_steps,
            "error": None,
        }

    except Exception as exc:
        latency_ms = (time.monotonic() - step_start) * 1000
        error_msg = f"generate_node failed: {exc}"
        logger.exception(error_msg)

        current_steps.append(
            {
                "step": step_name,
                "error": error_msg,
                "latency_ms": latency_ms,
            }
        )

        return {
            "draft_response": "",
            "generation_confidence": 0.0,
            "steps": current_steps,
            "error": error_msg,
        }
