"""Tool execution node — runs each selected tool and logs results."""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.agent.state import AgentState
from app.agent.tools.registry import get_tool

logger = logging.getLogger(__name__)


async def execute_node(
    state: AgentState,
    db: AsyncSession | None = None,
) -> dict[str, Any]:
    """Execute each tool selected by the decision node.

    Individual tool failures are isolated: one tool failing does not
    prevent the remaining tools from running.  All results — successes
    and failures alike — are collected into ``tool_results``.

    When a database session is provided, a ``ToolExecution`` record is
    persisted for every tool call (linked to the AgentLog for this step).

    Reads:
        ``selected_tools``, ``email``, ``tool_params``, ``trace_id``

    Writes:
        ``tool_results`` — mapping of tool_name -> result dict.
        ``steps``        — appended step trace entry.
        ``error``        — set only if every tool fails.
    """
    step_start = time.monotonic()
    step_name = "execute"
    current_steps: list[dict[str, Any]] = list(state.get("steps", []))

    selected_tools: list[str] = state.get("selected_tools", [])
    email: dict[str, Any] = state.get("email", {})
    tool_params: dict[str, dict[str, Any]] = state.get("tool_params", {})
    trace_id: str = state.get("trace_id", str(uuid.uuid4()))

    logger.info(
        "execute_node: starting — trace_id=%s tools=%s",
        trace_id,
        selected_tools,
    )

    tool_results: dict[str, Any] = {}
    tool_summaries: list[dict[str, Any]] = []
    agent_log_id: uuid.UUID | None = None

    # ------------------------------------------------------------------
    # Persist an AgentLog entry for this step so ToolExecution records
    # have a valid FK.  We do this before running tools.
    # ------------------------------------------------------------------
    if db is not None:
        try:
            from app.models import AgentLog  # noqa: PLC0415

            step_order = len(current_steps)
            agent_log = AgentLog(
                email_id=uuid.UUID(str(email.get("id", uuid.uuid4()))),
                trace_id=uuid.UUID(trace_id),
                step_name=step_name,
                step_order=step_order,
                input_state={
                    "selected_tools": selected_tools,
                    "tool_params": tool_params,
                },
            )
            db.add(agent_log)
            await db.flush()  # Populate agent_log.id without committing.
            agent_log_id = agent_log.id
        except Exception as exc:
            logger.warning("execute_node: failed to create AgentLog entry — %s", exc)

    # ------------------------------------------------------------------
    # Execute each tool
    # ------------------------------------------------------------------
    for tool_name in selected_tools:
        tool_fn = get_tool(tool_name)
        if tool_fn is None:
            logger.warning("execute_node: tool %r not found in registry; skipping", tool_name)
            tool_results[tool_name] = {"error": f"Tool '{tool_name}' not registered"}
            tool_summaries.append(
                {"tool": tool_name, "success": False, "error": "not registered"}
            )
            continue

        # Build params: start with any hints from the decision node, then
        # supplement with email fields that tools commonly need.
        params: dict[str, Any] = dict(tool_params.get(tool_name, {}))
        params.setdefault("email_id", email.get("id"))
        params.setdefault("sender", email.get("sender", ""))
        params.setdefault("to", email.get("sender", ""))
        params.setdefault("subject", f"Re: {email.get('subject', '')}")
        params.setdefault("thread_id", email.get("thread_id"))

        tool_start = time.monotonic()
        success = True
        result: dict[str, Any] = {}
        error_msg: str | None = None

        try:
            result = await tool_fn(params)
            tool_results[tool_name] = result
            logger.debug("execute_node: tool %r succeeded — %s", tool_name, result)
        except Exception as exc:
            success = False
            error_msg = str(exc)
            result = {"error": error_msg}
            tool_results[tool_name] = result
            logger.warning("execute_node: tool %r failed — %s", tool_name, exc)

        tool_latency_ms = (time.monotonic() - tool_start) * 1000
        tool_summaries.append(
            {
                "tool": tool_name,
                "success": success,
                "latency_ms": tool_latency_ms,
                **({"error": error_msg} if error_msg else {}),
            }
        )

        # ------------------------------------------------------------------
        # Persist ToolExecution record
        # ------------------------------------------------------------------
        if db is not None and agent_log_id is not None:
            try:
                from app.models import ToolExecution  # noqa: PLC0415

                te = ToolExecution(
                    agent_log_id=agent_log_id,
                    tool_name=tool_name,
                    params=params,
                    result=result,
                    success=success,
                    error_message=error_msg[:500] if error_msg else None,
                    latency_ms=tool_latency_ms,
                )
                db.add(te)
            except Exception as exc:
                logger.warning(
                    "execute_node: failed to persist ToolExecution for %r — %s",
                    tool_name,
                    exc,
                )

    # Flush ToolExecution records (they will be committed by the caller).
    if db is not None:
        try:
            await db.flush()
        except Exception as exc:
            logger.warning("execute_node: db flush failed — %s", exc)

    # ------------------------------------------------------------------
    # Finalise step trace
    # ------------------------------------------------------------------
    step_latency_ms = (time.monotonic() - step_start) * 1000
    all_failed = bool(selected_tools) and all(
        not s.get("success", True) for s in tool_summaries
    )
    error_out: str | None = (
        "All tool executions failed" if all_failed else None
    )

    current_steps.append(
        {
            "step": step_name,
            "tools": tool_summaries,
            "latency_ms": step_latency_ms,
            **({"error": error_out} if error_out else {}),
        }
    )

    logger.info(
        "execute_node: done — %d tools executed latency_ms=%.1f",
        len(selected_tools),
        step_latency_ms,
    )

    return {
        "tool_results": tool_results,
        "steps": current_steps,
        "error": error_out,
    }
