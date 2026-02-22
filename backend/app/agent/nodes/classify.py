"""Classification node — determines email intent and confidence score."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.agent.state import AgentState
from app.llm.client import get_gemini_client
from app.llm.utils import truncate_text

logger = logging.getLogger(__name__)

# Allowed classification categories (matches EmailClassification enum).
VALID_CATEGORIES = frozenset(
    {"inquiry", "meeting_request", "complaint", "follow_up", "spam", "other"}
)


async def classify_node(state: AgentState) -> dict[str, Any]:
    """Classify the intent of the incoming email.

    Reads ``state["email"]`` and writes:
        - ``classification``: intent category string
        - ``confidence``: float in [0, 1]
        - ``steps``: appended step trace entry
        - ``error``: set on failure

    Returns a partial state dict merged by LangGraph.
    """
    step_start = time.monotonic()
    step_name = "classify"
    current_steps: list[dict[str, Any]] = list(state.get("steps", []))

    email: dict[str, Any] = state.get("email", {})
    subject: str = email.get("subject", "")
    body: str = truncate_text(email.get("body", ""), max_chars=4000)
    sender: str = email.get("sender", "")

    logger.info(
        "classify_node: starting — trace_id=%s email_id=%s",
        state.get("trace_id", "unknown"),
        email.get("id", "unknown"),
    )

    try:
        client = get_gemini_client()
        result = await client.classify_intent(
            subject=subject,
            body=body,
            sender=sender,
        )

        # Normalise: guard against an LLM returning an unknown category.
        classification = result.intent.lower()
        if classification not in VALID_CATEGORIES:
            logger.warning(
                "classify_node: unknown category %r returned by LLM; defaulting to 'other'",
                classification,
            )
            classification = "other"

        confidence = max(0.0, min(1.0, result.confidence))

        latency_ms = (time.monotonic() - step_start) * 1000
        current_steps.append(
            {
                "step": step_name,
                "classification": classification,
                "confidence": confidence,
                "reasoning": result.reasoning,
                "latency_ms": latency_ms,
            }
        )

        logger.info(
            "classify_node: done — classification=%s confidence=%.3f latency_ms=%.1f",
            classification,
            confidence,
            latency_ms,
        )

        return {
            "classification": classification,
            "confidence": confidence,
            "steps": current_steps,
            "error": None,
        }

    except Exception as exc:
        latency_ms = (time.monotonic() - step_start) * 1000
        error_msg = f"classify_node failed: {exc}"
        logger.exception(error_msg)

        current_steps.append(
            {
                "step": step_name,
                "error": error_msg,
                "latency_ms": latency_ms,
            }
        )

        return {
            # Provide safe defaults so downstream nodes can still run if desired.
            "classification": "other",
            "confidence": 0.0,
            "steps": current_steps,
            "error": error_msg,
        }
