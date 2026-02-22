"""Decision node — selects tools based on email classification and context."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.agent.state import AgentState
from app.llm.client import get_gemini_client
from app.llm.utils import truncate_text

logger = logging.getLogger(__name__)

# Deterministic fallback tool mapping when the LLM is unavailable.
# Kept in sync with the rules defined in agent-workflow.md and prompts.py.
_FALLBACK_TOOLS: dict[str, list[str]] = {
    "meeting_request": ["check_calendar", "create_draft"],
    "complaint": ["get_contact", "create_draft"],
    "inquiry": ["get_contact", "create_draft"],
    "follow_up": ["get_contact", "create_draft"],
    "spam": [],
    "other": ["create_draft"],
}


async def decide_node(state: AgentState) -> dict[str, Any]:
    """Select which tools should be executed for this email.

    Delegates to ``GeminiClient.decide_tools`` for LLM-driven selection,
    with a deterministic fallback if the LLM call fails.

    Reads:
        ``classification``, ``email``, ``context``

    Writes:
        ``selected_tools`` — ordered list of tool names.
        ``tool_params``    — per-tool parameter hints from the LLM.
        ``steps``          — appended step trace entry.
        ``error``          — set on failure.
    """
    step_start = time.monotonic()
    step_name = "decide"
    current_steps: list[dict[str, Any]] = list(state.get("steps", []))

    classification: str = state.get("classification", "other")
    email: dict[str, Any] = state.get("email", {})
    context: list[str] = state.get("context", [])

    logger.info(
        "decide_node: starting — trace_id=%s classification=%s",
        state.get("trace_id", "unknown"),
        classification,
    )

    # Spam emails need no tools — short-circuit immediately.
    if classification == "spam":
        latency_ms = (time.monotonic() - step_start) * 1000
        current_steps.append(
            {
                "step": step_name,
                "selected_tools": [],
                "reasoning": "Spam emails require no tool execution.",
                "latency_ms": latency_ms,
            }
        )
        logger.info("decide_node: spam detected — no tools selected")
        return {
            "selected_tools": [],
            "tool_params": {},
            "steps": current_steps,
        }

    try:
        client = get_gemini_client()
        context_text = "\n".join(context) if context else "(no context)"
        # Truncate email body to avoid exceeding LLM context window.
        body = truncate_text(email.get("body", ""), max_chars=4000)
        result = await client.decide_tools(
            classification=classification,
            subject=email.get("subject", ""),
            body=body,
            context=context_text,
        )

        selected_tools = result.selected_tools
        tool_params = result.params

        latency_ms = (time.monotonic() - step_start) * 1000
        current_steps.append(
            {
                "step": step_name,
                "selected_tools": selected_tools,
                "reasoning": result.reasoning,
                "latency_ms": latency_ms,
            }
        )

        logger.info(
            "decide_node: done — tools=%s latency_ms=%.1f",
            selected_tools,
            latency_ms,
        )

        return {
            "selected_tools": selected_tools,
            "tool_params": tool_params,
            "steps": current_steps,
            "error": None,
        }

    except Exception as exc:
        # Fall back to deterministic rules so the pipeline can continue.
        fallback = _FALLBACK_TOOLS.get(classification, ["create_draft"])
        error_msg = f"decide_node LLM call failed ({exc}); using fallback tools: {fallback}"
        logger.warning(error_msg)

        latency_ms = (time.monotonic() - step_start) * 1000
        current_steps.append(
            {
                "step": step_name,
                "selected_tools": fallback,
                "fallback": True,
                "error": error_msg,
                "latency_ms": latency_ms,
            }
        )

        return {
            "selected_tools": fallback,
            "tool_params": {},
            "steps": current_steps,
            "error": error_msg,
        }
