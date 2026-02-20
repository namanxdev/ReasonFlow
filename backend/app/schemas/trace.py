"""Agent trace request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.models.email import EmailClassification
from app.schemas.common import PaginatedResponse


class ToolExecutionDetail(BaseModel):
    """Detail for a single tool invocation within an agent step."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Tool execution record identifier")
    tool_name: str = Field(description="Name of the tool that was invoked")
    params: dict[str, Any] | None = Field(
        default=None, description="Input parameters passed to the tool"
    )
    result: dict[str, Any] | None = Field(
        default=None, description="Output returned by the tool"
    )
    success: bool = Field(description="Whether the tool call succeeded")
    error_message: str | None = Field(
        default=None, description="Error description if the call failed"
    )
    latency_ms: float = Field(ge=0.0, description="Tool execution time in milliseconds")


class StepDetail(BaseModel):
    """Detail for one step in an agent workflow trace."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Agent log record identifier")
    step_name: str = Field(description="Workflow node name (e.g. 'classify', 'retrieve')")
    step_order: int = Field(ge=0, description="Execution order within the trace")
    input_state: dict[str, Any] | None = Field(
        default=None, description="Agent state entering this node"
    )
    output_state: dict[str, Any] | None = Field(
        default=None, description="Agent state exiting this node"
    )
    error_message: str | None = Field(
        default=None, description="Error message if this step failed"
    )
    latency_ms: float = Field(ge=0.0, description="Step execution time in milliseconds")
    tool_executions: list[ToolExecutionDetail] = Field(
        default_factory=list, description="Tool calls made during this step"
    )


class TraceResponse(BaseModel):
    """Summary of a single agent execution trace (used in list view)."""

    model_config = ConfigDict(from_attributes=True)

    trace_id: uuid.UUID = Field(description="Unique trace identifier")
    email_subject: str = Field(description="Subject of the email that was processed")
    classification: EmailClassification | None = Field(
        default=None, description="Agent-assigned email classification"
    )
    total_latency_ms: float = Field(
        ge=0.0, description="Total wall-clock time for the agent run in milliseconds"
    )
    step_count: int = Field(ge=0, description="Number of workflow steps executed")
    status: str = Field(description="Final trace status (e.g. 'completed', 'failed')")
    created_at: datetime = Field(description="When this trace was started")


class TraceEmailSummary(BaseModel):
    """Minimal email fields embedded inside a detailed trace response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    subject: str
    sender: str
    received_at: datetime
    classification: EmailClassification | None = None
    confidence: float | None = None


class TraceDetailResponse(BaseModel):
    """Full detail for a single trace, including all steps."""

    model_config = ConfigDict(from_attributes=True)

    trace_id: uuid.UUID = Field(description="Unique trace identifier")
    email: TraceEmailSummary = Field(description="Summary of the processed email")
    steps: list[StepDetail] = Field(
        default_factory=list,
        description="Ordered list of workflow steps",
    )
    total_latency_ms: float = Field(
        ge=0.0, description="Sum of all step latencies in milliseconds"
    )


# Convenience alias — traces list uses the same paginated wrapper.
TraceListResponse = PaginatedResponse[TraceResponse]
