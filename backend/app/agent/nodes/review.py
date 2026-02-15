"""Review node — decides whether to auto-approve or queue for human review."""

from __future__ import annotations

import logging
import time
from typing import Any

from app.agent.state import AgentState

logger = logging.getLogger(__name__)

# Confidence thresholds (from agent-engine.md and agent-workflow.md).
# The docs give slightly different thresholds (0.9/>0.7 vs 0.8).  We follow
# agent-workflow.md (the more detailed spec) and the agent-engine.md note that
# complaints *always* require approval.
AUTO_APPROVE_THRESHOLD = 0.8  # confidence >= this → auto-approve
FORCE_REVIEW_BELOW = 0.8      # confidence < this → require human review


async def review_node(state: AgentState) -> dict[str, Any]:
    """Determine whether the draft response can be auto-dispatched.

    Rules (in priority order):
      1. Classification is ``complaint`` → always require approval.
      2. Classification confidence < ``AUTO_APPROVE_THRESHOLD`` → require approval.
      3. Otherwise → auto-approve.

    When auto-approved, ``final_response`` is set to ``draft_response``
    so the dispatch node can send it immediately.

    Reads:
        ``draft_response``, ``confidence``, ``classification``

    Writes:
        ``requires_approval`` — bool flag for the conditional edge.
        ``final_response``    — populated only when auto-approved.
        ``steps``             — appended step trace entry.
    """
    step_start = time.monotonic()
    step_name = "review"
    current_steps: list[dict[str, Any]] = list(state.get("steps", []))

    classification: str = state.get("classification", "other")
    confidence: float = state.get("confidence", 0.0)
    draft_response: str = state.get("draft_response", "")

    logger.info(
        "review_node: starting — trace_id=%s classification=%s confidence=%.3f",
        state.get("trace_id", "unknown"),
        classification,
        confidence,
    )

    # Evaluate approval rules.
    is_complaint = classification == "complaint"
    low_confidence = confidence < AUTO_APPROVE_THRESHOLD

    requires_approval = is_complaint or low_confidence

    if requires_approval:
        reasons: list[str] = []
        if is_complaint:
            reasons.append("classification is 'complaint'")
        if low_confidence:
            reasons.append(f"confidence {confidence:.3f} < threshold {AUTO_APPROVE_THRESHOLD}")
        reasoning = "; ".join(reasons)
        final_response = ""
        logger.info("review_node: requires human approval — %s", reasoning)
    else:
        reasoning = (
            f"confidence {confidence:.3f} >= threshold {AUTO_APPROVE_THRESHOLD} "
            f"and classification is not 'complaint'"
        )
        final_response = draft_response
        logger.info("review_node: auto-approved — %s", reasoning)

    latency_ms = (time.monotonic() - step_start) * 1000
    current_steps.append(
        {
            "step": step_name,
            "requires_approval": requires_approval,
            "reasoning": reasoning,
            "latency_ms": latency_ms,
        }
    )

    return {
        "requires_approval": requires_approval,
        "final_response": final_response,
        "steps": current_steps,
    }
