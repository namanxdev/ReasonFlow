"""Pydantic schemas package — re-exports all public schemas."""

from app.schemas.auth import (
    GmailCallbackRequest,
    GmailCallbackResponse,
    GmailUrlResponse,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.schemas.calendar import (
    AvailabilityRequest,
    AvailabilityResponse,
    CreateEventRequest,
    EventResponse,
    TimeSlot,
)
from app.schemas.common import (
    ErrorResponse,
    PaginatedResponse,
    PaginationParams,
)
from app.schemas.crm import (
    ContactResponse,
    ContactUpdateRequest,
)
from app.schemas.draft import (
    DraftEditRequest,
    DraftListResponse,
    DraftResponse,
)
from app.schemas.email import (
    EmailDetailResponse,
    EmailFilterParams,
    EmailListResponse,
    EmailProcessRequest,
    EmailProcessResponse,
    EmailResponse,
)
from app.schemas.metrics import (
    IntentBucket,
    IntentMetrics,
    LatencyMetrics,
    LatencyPercentiles,
    MetricsDateRange,
    ToolMetricEntry,
    ToolMetrics,
)
from app.schemas.trace import (
    StepDetail,
    ToolExecutionDetail,
    TraceDetailResponse,
    TraceEmailSummary,
    TraceListResponse,
    TraceResponse,
)

__all__ = [
    # auth
    "RegisterRequest",
    "RegisterResponse",
    "LoginRequest",
    "TokenResponse",
    "RefreshRequest",
    "GmailCallbackRequest",
    "GmailUrlResponse",
    "GmailCallbackResponse",
    # common
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    # email
    "EmailResponse",
    "EmailDetailResponse",
    "EmailListResponse",
    "EmailFilterParams",
    "EmailProcessRequest",
    "EmailProcessResponse",
    # draft
    "DraftResponse",
    "DraftListResponse",
    "DraftEditRequest",
    # trace
    "ToolExecutionDetail",
    "StepDetail",
    "TraceResponse",
    "TraceEmailSummary",
    "TraceDetailResponse",
    "TraceListResponse",
    # metrics
    "MetricsDateRange",
    "IntentBucket",
    "IntentMetrics",
    "LatencyPercentiles",
    "LatencyMetrics",
    "ToolMetricEntry",
    "ToolMetrics",
    # calendar
    "AvailabilityRequest",
    "TimeSlot",
    "AvailabilityResponse",
    "CreateEventRequest",
    "EventResponse",
    # crm
    "ContactResponse",
    "ContactUpdateRequest",
]
