"""Metrics request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.email import EmailClassification


class MetricsDateRange(BaseModel):
    """Optional date-range filter shared by all metrics endpoints."""

    model_config = ConfigDict(extra="forbid")

    start: datetime | None = Field(
        default=None, description="Start of the reporting window (inclusive)"
    )
    end: datetime | None = Field(
        default=None, description="End of the reporting window (inclusive)"
    )

    @model_validator(mode="after")
    def end_must_be_after_start(self) -> MetricsDateRange:
        if self.start is not None and self.end is not None:
            if self.end < self.start:
                raise ValueError("'end' must be greater than or equal to 'start'")
        return self


class IntentBucket(BaseModel):
    """Count of agent runs for one email classification."""

    model_config = ConfigDict(extra="forbid")

    classification: EmailClassification = Field(description="Email classification label")
    count: int = Field(ge=0, description="Number of processed emails with this classification")
    percentage: float = Field(
        ge=0.0, le=100.0, description="Share of total (0–100)"
    )


class IntentMetrics(BaseModel):
    """Response for GET /metrics/intents — intent distribution over time."""

    model_config = ConfigDict(extra="forbid")

    total: int = Field(ge=0, description="Total emails processed in the period")
    buckets: list[IntentBucket] = Field(
        description="Per-classification breakdown"
    )
    start: datetime | None = Field(default=None, description="Reporting window start")
    end: datetime | None = Field(default=None, description="Reporting window end")


class LatencyPercentiles(BaseModel):
    """Latency distribution statistics in milliseconds."""

    model_config = ConfigDict(extra="forbid")

    p50: float = Field(ge=0.0, description="50th-percentile (median) latency in ms")
    p90: float = Field(ge=0.0, description="90th-percentile latency in ms")
    p99: float = Field(ge=0.0, description="99th-percentile latency in ms")
    mean: float = Field(ge=0.0, description="Mean latency in ms")
    min: float = Field(ge=0.0, description="Minimum observed latency in ms")
    max: float = Field(ge=0.0, description="Maximum observed latency in ms")


class LatencyMetrics(BaseModel):
    """Response for GET /metrics/latency — agent response latency statistics."""

    model_config = ConfigDict(extra="forbid")

    overall: LatencyPercentiles = Field(description="End-to-end agent latency stats")
    by_step: dict[str, LatencyPercentiles] = Field(
        default_factory=dict,
        description="Per-workflow-step latency breakdown keyed by step name",
    )
    sample_count: int = Field(ge=0, description="Number of traces included in this report")
    start: datetime | None = Field(default=None, description="Reporting window start")
    end: datetime | None = Field(default=None, description="Reporting window end")


class ToolMetricEntry(BaseModel):
    """Success-rate statistics for a single tool."""

    model_config = ConfigDict(extra="forbid")

    tool_name: str = Field(description="Tool identifier")
    total_calls: int = Field(ge=0, description="Total invocation count")
    successful_calls: int = Field(ge=0, description="Number of successful invocations")
    failed_calls: int = Field(ge=0, description="Number of failed invocations")
    success_rate: float = Field(
        ge=0.0, le=1.0, description="Fraction of calls that succeeded (0–1)"
    )
    mean_latency_ms: float = Field(ge=0.0, description="Mean tool execution time in ms")


class ToolMetrics(BaseModel):
    """Response for GET /metrics/tools — tool execution success rates."""

    model_config = ConfigDict(extra="forbid")

    tools: list[ToolMetricEntry] = Field(description="Per-tool statistics")
    start: datetime | None = Field(default=None, description="Reporting window start")
    end: datetime | None = Field(default=None, description="Reporting window end")


class SummaryStats(BaseModel):
    """Response for GET /metrics/summary — high-level KPI summary."""

    model_config = ConfigDict(extra="forbid")

    total_emails_processed: int = Field(ge=0, description="Total emails that have been processed")
    average_response_time_ms: float = Field(
        ge=0.0, description="Mean end-to-end agent latency in ms"
    )
    approval_rate: float = Field(
        ge=0.0, le=1.0, description="Fraction of drafts that were approved (0\u20131)"
    )
    human_review_rate: float = Field(
        ge=0.0, le=1.0, description="Fraction of drafts requiring human review (0\u20131)"
    )
