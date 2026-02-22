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


class AgentStateAccessor:
    """Type-safe accessor for AgentState.

    Provides property-based access to all AgentState fields with proper
    type hints, enabling IDE autocomplete and compile-time type checking.

    Example:
        >>> state: AgentState = {"email": {"subject": "Hello"}, "trace_id": "abc-123"}
        >>> s = AgentStateAccessor(state)
        >>> s.email.get("subject")  # Type-safe access
        'Hello'
        >>> s.classification = "inquiry"  # Type-safe assignment
    """

    def __init__(self, state: AgentState) -> None:
        """Initialize the accessor with an AgentState dictionary.

        Args:
            state: The AgentState TypedDict to wrap.
        """
        self._state = state

    # ------------------------------------------------------------------
    # Email
    # ------------------------------------------------------------------
    @property
    def email(self) -> dict[str, Any]:
        """Email data: id, subject, body, sender, received_at."""
        return self._state.get("email", {})

    @email.setter
    def email(self, value: dict[str, Any]) -> None:
        self._state["email"] = value

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------
    @property
    def classification(self) -> str | None:
        """Intent category: inquiry, meeting_request, complaint, follow_up, spam, other."""
        return self._state.get("classification")

    @classification.setter
    def classification(self, value: str) -> None:
        self._state["classification"] = value

    # ------------------------------------------------------------------
    # Confidence
    # ------------------------------------------------------------------
    @property
    def confidence(self) -> float | None:
        """Classification confidence score in range [0, 1]."""
        return self._state.get("confidence")

    @confidence.setter
    def confidence(self, value: float) -> None:
        self._state["confidence"] = value

    # ------------------------------------------------------------------
    # Context
    # ------------------------------------------------------------------
    @property
    def context(self) -> list[str]:
        """List of context strings from vector search, CRM, and calendar."""
        return self._state.get("context", [])

    @context.setter
    def context(self, value: list[str]) -> None:
        self._state["context"] = value

    # ------------------------------------------------------------------
    # Selected Tools
    # ------------------------------------------------------------------
    @property
    def selected_tools(self) -> list[str]:
        """List of tool names chosen by the decision node."""
        return self._state.get("selected_tools", [])

    @selected_tools.setter
    def selected_tools(self, value: list[str]) -> None:
        self._state["selected_tools"] = value

    # ------------------------------------------------------------------
    # Tool Results
    # ------------------------------------------------------------------
    @property
    def tool_results(self) -> dict[str, Any]:
        """Mapping of tool_name -> tool output from the execute node."""
        return self._state.get("tool_results", {})

    @tool_results.setter
    def tool_results(self, value: dict[str, Any]) -> None:
        self._state["tool_results"] = value

    # ------------------------------------------------------------------
    # Draft Response
    # ------------------------------------------------------------------
    @property
    def draft_response(self) -> str | None:
        """Email response draft produced by the generate node."""
        return self._state.get("draft_response")

    @draft_response.setter
    def draft_response(self, value: str) -> None:
        self._state["draft_response"] = value

    # ------------------------------------------------------------------
    # Requires Approval
    # ------------------------------------------------------------------
    @property
    def requires_approval(self) -> bool | None:
        """True when a human must review the draft before dispatch."""
        return self._state.get("requires_approval")

    @requires_approval.setter
    def requires_approval(self, value: bool) -> None:
        self._state["requires_approval"] = value

    # ------------------------------------------------------------------
    # Final Response
    # ------------------------------------------------------------------
    @property
    def final_response(self) -> str | None:
        """The approved response text that will be sent via Gmail."""
        return self._state.get("final_response")

    @final_response.setter
    def final_response(self, value: str) -> None:
        self._state["final_response"] = value

    # ------------------------------------------------------------------
    # Error
    # ------------------------------------------------------------------
    @property
    def error(self) -> str | None:
        """Error message set when a node fails; None when healthy."""
        return self._state.get("error")

    @error.setter
    def error(self, value: str | None) -> None:
        self._state["error"] = value

    # ------------------------------------------------------------------
    # Steps
    # ------------------------------------------------------------------
    @property
    def steps(self) -> list[dict[str, Any]]:
        """Execution trace — one entry per node for observability."""
        return self._state.get("steps", [])

    @steps.setter
    def steps(self, value: list[dict[str, Any]]) -> None:
        self._state["steps"] = value

    # ------------------------------------------------------------------
    # Trace ID
    # ------------------------------------------------------------------
    @property
    def trace_id(self) -> str:
        """UUID string grouping all AgentLog entries for one processing run."""
        return self._state.get("trace_id", "")

    @trace_id.setter
    def trace_id(self, value: str) -> None:
        self._state["trace_id"] = value

    # ------------------------------------------------------------------
    # Tool Params
    # ------------------------------------------------------------------
    @property
    def tool_params(self) -> dict[str, dict[str, Any]]:
        """Optional per-tool parameter hints from the decision node."""
        return self._state.get("tool_params", {})

    @tool_params.setter
    def tool_params(self, value: dict[str, dict[str, Any]]) -> None:
        self._state["tool_params"] = value

    # ------------------------------------------------------------------
    # Generation Confidence
    # ------------------------------------------------------------------
    @property
    def generation_confidence(self) -> float | None:
        """Confidence score from generation node (separate from classification)."""
        return self._state.get("generation_confidence")

    @generation_confidence.setter
    def generation_confidence(self, value: float) -> None:
        self._state["generation_confidence"] = value

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------
    def to_dict(self) -> AgentState:
        """Return the underlying state dictionary.

        Returns:
            The wrapped AgentState dictionary.
        """
        return self._state

    def copy(self) -> AgentState:
        """Return a shallow copy of the underlying state dictionary.

        Returns:
            A shallow copy of the AgentState.
        """
        return self._state.copy()
