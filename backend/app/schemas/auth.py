"""Authentication request/response schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    """Request body for POST /auth/register."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(description="New account email address")
    password: str = Field(
        min_length=8,
        description="Account password (minimum 8 characters)",
    )


class LoginRequest(BaseModel):
    """Request body for POST /auth/login."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(description="Account email address")
    password: str = Field(description="Account password")


class TokenResponse(BaseModel):
    """Response body for POST /auth/login — contains the issued JWT."""

    model_config = ConfigDict(extra="forbid")

    access_token: str = Field(description="Signed JWT access token")
    token_type: str = Field(default="bearer", description="Token scheme (always 'bearer')")
    expires_in: int | None = Field(
        default=None,
        description="Token lifetime in seconds (omitted on refresh responses)",
    )


class TokenResponseWithRefresh(TokenResponse):
    """Response including refresh token - for secure cookie-based auth."""

    refresh_token: str | None = Field(
        default=None,
        description="Signed JWT refresh token (only returned when not using cookies)",
    )


class RegisterResponse(BaseModel):
    """Response body for POST /auth/register — user record plus initial token."""

    model_config = ConfigDict(extra="forbid")

    id: uuid.UUID = Field(description="New user identifier")
    email: EmailStr = Field(description="Registered email address")
    access_token: str = Field(description="Signed JWT access token")
    token_type: str = Field(default="bearer", description="Token scheme (always 'bearer')")


class RefreshRequest(BaseModel):
    """Request body for POST /auth/refresh.

    The token to refresh is read from the Authorization header in the
    FastAPI route handler; this schema is provided for completeness and
    future use (e.g. an explicit refresh-token field).
    """

    model_config = ConfigDict(extra="forbid")


class GmailCallbackRequest(BaseModel):
    """Request body for POST /auth/gmail/callback."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(description="OAuth 2.0 authorization code returned by Google")

    @field_validator("code")
    @classmethod
    def code_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("OAuth code must not be blank")
        return v


class GmailUrlResponse(BaseModel):
    """Response body for GET /auth/gmail/url."""

    model_config = ConfigDict(extra="forbid")

    url: str = Field(description="Google OAuth consent URL")


class GmailCallbackResponse(BaseModel):
    """Response body for POST /auth/gmail/callback."""

    model_config = ConfigDict(extra="forbid")

    status: str = Field(description="Connection status (e.g. 'connected')")
    email: EmailStr = Field(description="Gmail address that was connected")
    access_token: str | None = Field(
        default=None,
        description="JWT access token (returned only for unauthenticated Gmail login flow)",
    )
    token_type: str | None = Field(
        default=None,
        description="Token scheme, 'bearer' when access_token is present",
    )


class ForgotPasswordRequest(BaseModel):
    """Request body for POST /auth/forgot-password."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr = Field(description="Account email address")


class ResetPasswordRequest(BaseModel):
    """Request body for POST /auth/reset-password."""

    model_config = ConfigDict(extra="forbid")

    token: str = Field(description="Password reset token from email")
    new_password: str = Field(
        min_length=8,
        description="New account password (minimum 8 characters)",
    )
