"""Common/shared schemas used across multiple endpoints."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Query parameters for paginated list endpoints."""

    model_config = ConfigDict(extra="forbid")

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    per_page: int = Field(default=20, ge=1, le=100, description="Items per page")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: list[T]
    total: int = Field(ge=0, description="Total number of matching records")
    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, description="Items returned per page")


class ErrorResponse(BaseModel):
    """Standard error response body."""

    model_config = ConfigDict(extra="forbid")

    detail: str = Field(description="Human-readable error description")
    code: str | None = Field(
        default=None, description="Machine-readable error code, if available"
    )
    extra: dict[str, Any] | None = Field(
        default=None, description="Additional context about the error"
    )
