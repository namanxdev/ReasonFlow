"""LangGraph workflow graph for the ReasonFlow email processing agent.

Builds and compiles a ``StateGraph`` that runs emails through a 7-node
pipeline with conditional routing after the review step.

Entry point::

    from app.agent.graph import process_email

    final_state = await process_email(email_id=uuid_obj, db_session=session)
"""

from __future__ import annotations

import logging
import time
import uuid
from functools import partial
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.nodes.classify import classify_node
from app.agent.nodes.decide import decide_node
from app.agent.nodes.dispatch import dispatch_node
from app.agent.nodes.execute import execute_node
from app.agent.nodes.generate import generate_node
from app.agent.nodes.retrieve import retrieve_node
from app.agent.nodes.review import review_node
from app.agent.state import AgentState

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Conditional edge — routing after the review node
# ---------------------------------------------------------------------------


def _route_after_review(state: AgentState) -> Literal["dispatch", "human_queue"]:
    """Return the next node name based on the review decision.

    - ``dispatch``    → confidence >= 0.8 and not a complaint.
    - ``human_queue`` → requires human approval.

    LangGraph uses the returned string to look up the next node in the
    graph's conditional edge mapping.
    """
    if state.get("requires_approval", True):
        return "human_queue"
    return "dispatch"


def _route_after_classify(state: AgentState) -> str:
    """Short-circuit spam emails with high confidence directly to END.

    Returns the string ``"__end__"`` (the value of ``langgraph.graph.END``) for
    high-confidence spam so the graph terminates without further processing.
    Otherwise returns ``"retrieve"`` to continue the pipeline.
    """
    classification = state.get("classification", "other")
    confidence = state.get("confidence", 0.0)
    if classification == "spam" and confidence >= 0.8:
        logger.info(
            "graph: spam detected with confidence=%.3f — short-circuiting to END", confidence
        )
        return END
    return "retrieve"


def _route_after_decide(state: AgentState) -> Literal["execute", "generate"]:
    """Skip tool execution when no tools are selected."""
    if state.get("selected_tools"):
        return "execute"
    return "generate"


# ---------------------------------------------------------------------------
# Human queue pseudo-node
# ---------------------------------------------------------------------------


async def human_queue_node(state: AgentState) -> dict[str, Any]:
    """Pseudo-node that marks the email as needing human review.

    In the current implementation this records the queue action in the
    execution trace.  A real system would push a task to Redis / a task
    queue here.
    """
    logger.info(
        "human_queue_node: email queued for human review — trace_id=%s",
        state.get("trace_id", "unknown"),
    )
    current_steps: list[dict[str, Any]] = list(state.get("steps", []))
    current_steps.append(
        {
            "step": "human_queue",
            "action": "queued_for_review",
            "requires_approval": True,
        }
    )
    return {"steps": current_steps}


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------


def _build_graph(db: AsyncSession | None = None) -> Any:
    """Build and compile the StateGraph.

    Nodes that need database access receive it via ``functools.partial`` so
    the graph remains stateless between invocations.

    Args:
        db: Optional async database session injected at graph build time.

    Returns:
        A compiled LangGraph ``CompiledGraph`` ready for ``.ainvoke()``.
    """
    graph = StateGraph(AgentState)

    # ------------------------------------------------------------------
    # Register nodes
    # ------------------------------------------------------------------
    graph.add_node("classify", classify_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("decide", decide_node)
    graph.add_node(
        "execute",
        partial(execute_node, db=db),
    )
    graph.add_node("generate", generate_node)
    graph.add_node("review", review_node)
    graph.add_node(
        "dispatch",
        partial(dispatch_node, db=db),
    )
    graph.add_node("human_queue", human_queue_node)

    # ------------------------------------------------------------------
    # Define edges
    # ------------------------------------------------------------------
    graph.add_edge(START, "classify")

    # After classify: skip to END for high-confidence spam, else continue.
    graph.add_conditional_edges(
        "classify",
        _route_after_classify,
        {"retrieve": "retrieve", END: END},
    )

    graph.add_edge("retrieve", "decide")

    # After decide: skip execute when no tools are selected.
    graph.add_conditional_edges(
        "decide",
        _route_after_decide,
        {"execute": "execute", "generate": "generate"},
    )

    graph.add_edge("execute", "generate")
    graph.add_edge("generate", "review")

    # After review: dispatch immediately or send to human queue.
    graph.add_conditional_edges(
        "review",
        _route_after_review,
        {"dispatch": "dispatch", "human_queue": "human_queue"},
    )

    graph.add_edge("dispatch", END)
    graph.add_edge("human_queue", END)

    return graph.compile()


# ---------------------------------------------------------------------------
# AgentLog helpers
# ---------------------------------------------------------------------------


async def _log_agent_step(
    db: AsyncSession,
    email_id: uuid.UUID,
    trace_id: uuid.UUID,
    step_name: str,
    step_order: int,
    input_state: dict[str, Any],
    output_state: dict[str, Any],
    error_message: str | None,
    latency_ms: float,
) -> None:
    """Persist a single AgentLog entry."""
    try:
        from app.models import AgentLog  # noqa: PLC0415

        log_entry = AgentLog(
            email_id=email_id,
            trace_id=trace_id,
            step_name=step_name,
            step_order=step_order,
            input_state=input_state,
            output_state=output_state,
            error_message=error_message,
            latency_ms=latency_ms,
        )
        db.add(log_entry)
        await db.flush()
    except Exception as exc:
        logger.warning("Failed to persist AgentLog for step %r: %s", step_name, exc)


async def _persist_trace(
    db: AsyncSession | None,
    email_id: uuid.UUID,
    trace_id: uuid.UUID,
    steps: list[dict[str, Any]],
    total_latency_ms: float,
) -> None:
    """Write one AgentLog entry per step in the execution trace."""
    if db is None:
        return

    for order, step in enumerate(steps):
        step_name = step.get("step", f"step_{order}")
        error_msg: str | None = step.get("error")
        latency = float(step.get("latency_ms", 0.0))

        await _log_agent_step(
            db=db,
            email_id=email_id,
            trace_id=trace_id,
            step_name=step_name,
            step_order=order,
            input_state={},  # Individual node I/O is captured inside each node.
            output_state=step,
            error_message=error_msg,
            latency_ms=latency,
        )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


async def process_email(
    email_id: uuid.UUID,
    db_session: AsyncSession,
) -> AgentState:
    """Run the email processing pipeline for the given email.

    This is the primary external interface of the agent engine.

    Args:
        email_id:   The UUID of the email to process.
        db_session: An open ``AsyncSession`` used for database reads/writes.

    Returns:
        The final ``AgentState`` produced by the graph run.
    """
    run_start = time.monotonic()
    trace_id = uuid.uuid4()

    logger.info(
        "process_email: starting — email_id=%s trace_id=%s",
        email_id,
        trace_id,
    )

    # ------------------------------------------------------------------
    # Load the email record from the database.
    # ------------------------------------------------------------------
    from app.models.email import Email, EmailStatus  # noqa: PLC0415

    result = await db_session.execute(select(Email).where(Email.id == email_id))
    email_record = result.scalar_one_or_none()

    if email_record is None:
        raise ValueError(f"Email with id={email_id} not found in the database.")

    # Mark the email as processing.
    email_record.status = EmailStatus.PROCESSING
    await db_session.flush()

    email_dict: dict[str, Any] = {
        "id": str(email_record.id),
        "user_id": str(email_record.user_id),
        "gmail_id": email_record.gmail_id,
        "thread_id": email_record.thread_id,
        "subject": email_record.subject,
        "body": email_record.body,
        "sender": email_record.sender,
        "recipient": email_record.recipient,
        "received_at": (
            email_record.received_at.isoformat()
            if email_record.received_at
            else ""
        ),
    }

    # ------------------------------------------------------------------
    # Build the initial state.
    # ------------------------------------------------------------------
    initial_state: AgentState = {
        "email": email_dict,
        "classification": "",
        "confidence": 0.0,
        "context": [],
        "selected_tools": [],
        "tool_results": {},
        "draft_response": "",
        "requires_approval": True,
        "final_response": "",
        "error": None,
        "steps": [],
        "trace_id": str(trace_id),
        "tool_params": {},
        "generation_confidence": 0.0,
    }

    # ------------------------------------------------------------------
    # Compile and run the graph.
    # ------------------------------------------------------------------
    compiled = _build_graph(db=db_session)

    try:
        final_state: AgentState = await compiled.ainvoke(initial_state)
    except Exception as exc:
        error_msg = f"process_email graph execution failed: {exc}"
        logger.exception(error_msg)
        # Update email status to needs_review so a human can intervene.
        email_record.status = EmailStatus.NEEDS_REVIEW
        await db_session.flush()
        # Return a minimal error state.
        final_state = {
            **initial_state,
            "error": error_msg,
        }

    # ------------------------------------------------------------------
    # Update email record with results from the final state.
    # ------------------------------------------------------------------
    try:
        classification_str = final_state.get("classification", "")
        if classification_str:
            from app.models.email import EmailClassification  # noqa: PLC0415

            try:
                email_record.classification = EmailClassification(classification_str)
            except ValueError:
                pass  # Unknown category — leave classification as-is.

        email_record.confidence = final_state.get("confidence", 0.0)

        if final_state.get("draft_response"):
            email_record.draft_response = final_state["draft_response"]

        # Status is updated by the dispatch node; only update here when it
        # hasn't been updated by dispatch (e.g. spam short-circuit).
        if email_record.status == EmailStatus.PROCESSING:
            email_record.status = EmailStatus.DRAFTED

        await db_session.flush()
    except Exception as exc:
        logger.warning("process_email: failed to update email record — %s", exc)

    # ------------------------------------------------------------------
    # Persist the full execution trace to agent_logs.
    # ------------------------------------------------------------------
    total_latency_ms = (time.monotonic() - run_start) * 1000
    await _persist_trace(
        db=db_session,
        email_id=email_id,
        trace_id=trace_id,
        steps=final_state.get("steps", []),
        total_latency_ms=total_latency_ms,
    )

    try:
        await db_session.commit()
    except Exception as exc:
        logger.warning("process_email: db commit failed — %s", exc)
        await db_session.rollback()

    logger.info(
        "process_email: complete — email_id=%s trace_id=%s latency_ms=%.1f error=%s",
        email_id,
        trace_id,
        total_latency_ms,
        final_state.get("error"),
    )

    return final_state
