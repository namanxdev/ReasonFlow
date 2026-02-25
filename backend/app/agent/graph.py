"""LangGraph workflow graph for the ReasonFlow email processing agent.

Builds and compiles a ``StateGraph`` that runs emails through a 7-node
pipeline with conditional routing after the review step.

Entry point::

    from app.agent.graph import process_email

    final_state = await process_email(email_id=uuid_obj, db_session=session)
"""

from __future__ import annotations

import asyncio
import logging
import time
import uuid
from collections.abc import Callable
from functools import partial, wraps
from typing import Any, Literal

from fastapi import HTTPException
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
from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Compiled graph cache
# ---------------------------------------------------------------------------

_compiled_graph: Any | None = None
_graph_lock = asyncio.Lock()


async def get_compiled_graph(db: AsyncSession | None = None) -> Any:
    """Get or create cached compiled graph.

    This function implements a thread-safe singleton pattern for the compiled
    LangGraph. The graph is built once and cached at module level to avoid
    rebuilding on every email processing request.

    Args:
        db: Optional async database session injected at graph build time.

    Returns:
        A compiled LangGraph ``CompiledGraph`` ready for ``.ainvoke()``.
    """
    global _compiled_graph

    if _compiled_graph is not None:
        return _compiled_graph

    async with _graph_lock:
        # Double-check pattern to prevent race conditions
        if _compiled_graph is not None:
            return _compiled_graph

        _compiled_graph = _build_graph(db)
        return _compiled_graph

# ---------------------------------------------------------------------------
# Critical vs recoverable nodes
# ---------------------------------------------------------------------------

# Nodes that are CRITICAL - graph fails completely if these fail
CRITICAL_NODES: set[str] = {"classify", "generate"}

# Nodes that are RECOVERABLE - errors are logged but graph continues
RECOVERABLE_NODES: set[str] = {"retrieve", "decide", "execute", "review", "dispatch"}

# ---------------------------------------------------------------------------
# Error handling wrapper
# ---------------------------------------------------------------------------


class NodeError(Exception):
    """Exception raised when a critical node fails."""

    def __init__(self, node_name: str, original_error: Exception) -> None:
        self.node_name = node_name
        self.original_error = original_error
        super().__init__(f"Critical node '{node_name}' failed: {original_error}")


def _wrap_node_with_error_handling(
    node_fn: Callable[..., Any],
    node_name: str,
    is_critical: bool = False,
) -> Callable[..., Any]:
    """Wrap a node function with error handling and recovery logic.

    This wrapper ensures that:
    1. Node exceptions are caught and logged
    2. Recoverable errors return safe defaults so the graph continues
    3. Critical errors raise NodeError to halt the entire pipeline

    Args:
        node_fn: The original node function to wrap
        node_name: Name of the node for logging purposes
        is_critical: If True, failures raise NodeError; if False, returns safe defaults

    Returns:
        A wrapped async function with error handling
    """

    @wraps(node_fn)
    async def _wrapped_node(state: AgentState, **kwargs: Any) -> dict[str, Any]:
        step_start = time.monotonic()
        trace_id = state.get("trace_id", "unknown")

        logger.debug("_wrap_node: starting — node=%s trace_id=%s", node_name, trace_id)

        try:
            # Attempt to run the original node function
            result = await node_fn(state, **kwargs)

            # Ensure result is a dict
            if not isinstance(result, dict):
                logger.warning(
                    "_wrap_node: node %s returned non-dict result, wrapping — trace_id=%s",
                    node_name,
                    trace_id,
                )
                result = {"_node_result": result}

            latency_ms = (time.monotonic() - step_start) * 1000
            logger.debug(
                "_wrap_node: success — node=%s trace_id=%s latency_ms=%.1f",
                node_name,
                trace_id,
                latency_ms,
            )

            return result

        except Exception as exc:
            latency_ms = (time.monotonic() - step_start) * 1000
            error_msg = f"Node {node_name} failed: {exc}"
            logger.exception(
                "_wrap_node: error — node=%s trace_id=%s latency_ms=%.1f error=%s",
                node_name,
                trace_id,
                latency_ms,
                exc,
            )

            if is_critical:
                # Critical node failure - halt the entire pipeline
                logger.error(
                    "_wrap_node: critical node %s failed, halting pipeline — trace_id=%s",
                    node_name,
                    trace_id,
                )
                raise NodeError(node_name, exc) from exc

            # Recoverable node failure - return safe defaults with error info
            current_steps: list[dict[str, Any]] = list(state.get("steps", []))
            current_steps.append(
                {
                    "step": node_name,
                    "error": error_msg,
                    "latency_ms": latency_ms,
                    "recovered": True,
                }
            )

            # Build safe defaults based on node type
            safe_defaults = _get_safe_defaults_for_node(node_name, state)
            safe_defaults["steps"] = current_steps
            safe_defaults["error"] = error_msg

            logger.warning(
                "_wrap_node: recovered from %s failure, continuing — trace_id=%s",
                node_name,
                trace_id,
            )

            return safe_defaults

    return _wrapped_node


def _get_safe_defaults_for_node(node_name: str, state: AgentState) -> dict[str, Any]:
    """Return safe default values for a given node when it fails.

    These defaults allow the pipeline to continue with degraded functionality
    rather than failing completely.

    Args:
        node_name: Name of the node that failed
        state: Current agent state

    Returns:
        Dictionary with safe default values for the node's outputs
    """
    defaults: dict[str, Any] = {}

    if node_name == "retrieve":
        # Failed retrieval: continue with empty context
        defaults["context"] = []

    elif node_name == "decide":
        # Failed decision: use classification-based fallback tools
        classification = state.get("classification", "other")
        fallback_tools: dict[str, list[str]] = {
            "meeting_request": ["check_calendar", "create_draft"],
            "complaint": ["get_contact", "create_draft"],
            "inquiry": ["get_contact", "create_draft"],
            "follow_up": ["get_contact", "create_draft"],
            "spam": [],
            "other": ["create_draft"],
        }
        defaults["selected_tools"] = fallback_tools.get(classification, ["create_draft"])
        defaults["tool_params"] = {}

    elif node_name == "execute":
        # Failed execution: continue with empty tool results
        defaults["tool_results"] = {}

    elif node_name == "review":
        # Failed review: default to requiring human approval (safe fallback)
        defaults["requires_approval"] = True
        defaults["review_confidence"] = 0.0
        defaults["review_reasoning"] = "Review node failed - defaulting to human approval"

    elif node_name == "dispatch":
        # Failed dispatch: mark as needing review so human can retry
        defaults["final_response"] = ""
        # Note: dispatch failure should mark email status as needs_review
        # This is handled by the caller (process_email)

    elif node_name == "human_queue":
        # Failed human queue: just continue
        pass

    return defaults


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
    execution trace.  A real system would push a task to a task
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

    All nodes are wrapped with error handling to enable graceful degradation:
    - Critical nodes (classify, generate) halt the pipeline on failure
    - Recoverable nodes (retrieve, decide, execute, review, dispatch) return
      safe defaults and allow the pipeline to continue

    Args:
        db: Optional async database session injected at graph build time.

    Returns:
        A compiled LangGraph ``CompiledGraph`` ready for ``.ainvoke()``.
    """
    graph = StateGraph(AgentState)

    # ------------------------------------------------------------------
    # Register nodes with error handling wrappers
    # ------------------------------------------------------------------

    # Critical nodes - pipeline halts on failure
    graph.add_node(
        "classify",
        _wrap_node_with_error_handling(classify_node, "classify", is_critical=True),
    )
    graph.add_node(
        "generate",
        _wrap_node_with_error_handling(generate_node, "generate", is_critical=True),
    )

    # Recoverable nodes - return safe defaults on failure, pipeline continues
    graph.add_node(
        "retrieve",
        _wrap_node_with_error_handling(retrieve_node, "retrieve", is_critical=False),
    )
    graph.add_node(
        "decide",
        _wrap_node_with_error_handling(decide_node, "decide", is_critical=False),
    )
    graph.add_node(
        "execute",
        _wrap_node_with_error_handling(
            partial(execute_node, db=db),
            "execute",
            is_critical=False,
        ),
    )
    graph.add_node(
        "review",
        _wrap_node_with_error_handling(review_node, "review", is_critical=False),
    )
    graph.add_node(
        "dispatch",
        _wrap_node_with_error_handling(
            partial(dispatch_node, db=db),
            "dispatch",
            is_critical=False,
        ),
    )
    graph.add_node(
        "human_queue",
        _wrap_node_with_error_handling(human_queue_node, "human_queue", is_critical=False),
    )

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


async def _handle_timeout(email_id: uuid.UUID, db_session: AsyncSession) -> None:
    """Update email status to needs_review when the pipeline times out.

    Args:
        email_id: The UUID of the email that timed out.
        db_session: An open AsyncSession for database writes.
    """
    from app.models.email import Email, EmailStatus  # noqa: PLC0415

    result = await db_session.execute(select(Email).where(Email.id == email_id))
    email_record = result.scalar_one_or_none()

    if email_record is not None:
        email_record.status = EmailStatus.NEEDS_REVIEW
        await db_session.flush()
        logger.info(
            "_handle_timeout: email status updated to needs_review — email_id=%s",
            email_id,
        )


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

    Raises:
        HTTPException: If the pipeline times out (504 Gateway Timeout).
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

    # Email is already in PROCESSING state — set by email_service.process_email

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
    # Compile and run the graph with timeout.
    # ------------------------------------------------------------------
    compiled = await get_compiled_graph(db=db_session)

    try:
        final_state: AgentState = await asyncio.wait_for(
            compiled.ainvoke(initial_state),
            timeout=settings.AGENT_PIPELINE_TIMEOUT,
        )
    except TimeoutError:
        logger.error(
            "Agent pipeline timed out for email_id=%s after %.1f seconds",
            email_id,
            settings.AGENT_PIPELINE_TIMEOUT,
        )
        # Update email status to needs_review so a human can intervene.
        await _handle_timeout(email_id, db_session)
        await db_session.commit()
        raise HTTPException(
            status_code=504,
            detail="Email processing timed out",
        )
    except NodeError as node_exc:
        # Critical node failure - entire pipeline halted
        error_msg = (
            f"process_email: critical node '{node_exc.node_name}' failed — "
            f"{node_exc.original_error}"
        )
        logger.exception(error_msg)
        # Update email status to needs_review so a human can intervene.
        email_record.status = EmailStatus.NEEDS_REVIEW
        await db_session.flush()
        # Return a minimal error state.
        final_state = {
            **initial_state,
            "error": error_msg,
            "failed_node": node_exc.node_name,
        }
    except Exception as exc:
        # Unexpected error (should rarely happen with per-node error handling)
        error_msg = f"process_email: unexpected graph execution failure: {exc}"
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
