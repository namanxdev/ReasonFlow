"""AgentState definition for the LangGraph email processing pipeline."""

from __future__ import annotations

from typing import Any, TypedDict


class AgentState(TypedDict, total=False):
    """State shared across all nodes in the email processing graph.

    Fields
    ------
    email:
        Dict containing email data: id, subject, body, sender, received_at.
    classification:
        Intent category assigned by the classify node.
        One of: inquiry, meeting_request, complaint, follow_up, spam, other.
    confidence:
        Classification confidence score in the range [0, 1].
    context:
        List of context strings retrieved from vector search, CRM, and calendar.
    selected_tools:
        List of tool names chosen by the decision node.
    tool_results:
        Mapping of tool_name -> tool output produced by the execute node.
    draft_response:
        Email response draft produced by the generate node.
    requires_approval:
        True when a human must review the draft before dispatch.
    final_response:
        The approved response text that will be sent via Gmail.
    error:
        Error message set when a node fails; None when everything is healthy.
    steps:
        Execution trace — one entry per node, written by each node for
        observability.
    trace_id:
        UUID string grouping all AgentLog entries for one processing run.
    tool_params:
        Optional per-tool parameter hints produced by the decision node.
    generation_confidence:
        Confidence score returned by the generation node (separate from the
        classification confidence used for routing decisions).
    """

    email: dict[str, Any]
    classification: str
    confidence: float
    context: list[str]
    selected_tools: list[str]
    tool_results: dict[str, Any]
    draft_response: str
    requires_approval: bool
    final_response: str
    error: str | None
    steps: list[dict[str, Any]]
    trace_id: str
    tool_params: dict[str, dict[str, Any]]
    generation_confidence: float
