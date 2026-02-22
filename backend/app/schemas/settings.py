"""Settings/Preferences request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime
from zoneinfo import available_timezones

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Cache available timezones for performance
_AVAILABLE_TIMEZONES = available_timezones()


class UserPreferencesResponse(BaseModel):
    """User preferences as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Preferences record identifier")
    user_id: uuid.UUID = Field(description="Associated user identifier")
    auto_approval_threshold: float = Field(
        default=0.9,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for auto-approving responses (0.0-1.0)",
    )
    email_sync_frequency_minutes: int = Field(
        default=15,
        ge=1,
        le=1440,
        description="Email sync frequency in minutes (1-1440)",
    )
    notification_settings: dict = Field(
        default_factory=dict,
        description="Notification preferences (email, push, digest)",
    )
    timezone: str = Field(
        default="UTC",
        description="User timezone (IANA identifier)",
    )
    daily_digest_enabled: bool = Field(
        default=True,
        description="Whether daily digest emails are enabled",
    )
    auto_classify_on_sync: bool = Field(
        default=True,
        description="Automatically classify emails during sync",
    )
    max_auto_responses_per_day: int = Field(
        default=50,
        ge=0,
        le=1000,
        description="Maximum auto-responses allowed per day (0-1000)",
    )
    created_at: datetime = Field(description="Record creation timestamp")
    updated_at: datetime = Field(description="Record last update timestamp")


class UserPreferencesUpdateRequest(BaseModel):
    """Request body for updating user preferences (partial update)."""

    model_config = ConfigDict(extra="forbid")

    auto_approval_threshold: float | None = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence threshold for auto-approving responses (0.0-1.0)",
    )
    email_sync_frequency_minutes: int | None = Field(
        default=None,
        ge=1,
        le=1440,
        description="Email sync frequency in minutes (1-1440)",
    )
    notification_settings: dict | None = Field(
        default=None,
        description="Notification preferences (email, push, digest)",
    )
    timezone: str | None = Field(
        default=None,
        max_length=100,
        description="User timezone (IANA identifier)",
    )
    daily_digest_enabled: bool | None = Field(
        default=None,
        description="Whether daily digest emails are enabled",
    )
    auto_classify_on_sync: bool | None = Field(
        default=None,
        description="Automatically classify emails during sync",
    )
    max_auto_responses_per_day: int | None = Field(
        default=None,
        ge=0,
        le=1000,
        description="Maximum auto-responses allowed per day (0-1000)",
    )

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str | None) -> str | None:
        """Validate timezone is a valid IANA timezone identifier.
        
        Uses Python 3.9+ zoneinfo module with IANA timezone database.
        On Windows, requires 'tzdata' package to be installed.
        """
        if v is None:
            return v
        # Check against cached timezone set (empty on Windows without tzdata)
        if _AVAILABLE_TIMEZONES and v not in _AVAILABLE_TIMEZONES:
            raise ValueError(f"Invalid timezone: {v}. Must be a valid IANA timezone.")
        return v
