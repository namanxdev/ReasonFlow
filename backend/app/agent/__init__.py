"""Agent engine package for ReasonFlow.

Exposes the LangGraph-based email processing workflow and the
AgentState type used throughout the pipeline.
"""

from __future__ import annotations

from app.agent.graph import process_email
from app.agent.state import AgentState

__all__ = ["process_email", "AgentState"]
