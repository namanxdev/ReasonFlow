"""Authentication API routes."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, oauth2_scheme
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    decode_token,
    hash_password,
)
from app.integrations.gmail.oauth import get_oauth_url
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    GmailCallbackRequest,
    GmailCallbackResponse,
    GmailUrlResponse,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    ResetPasswordRequest,
    TokenResponse,
)
from app.api.middleware.rate_limit import auth_rate_limit
from app.services import auth_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
    dependencies=[Depends(auth_rate_limit)],
)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> RegisterResponse:
    """Register a new user and return an initial access token."""
    user = await auth_service.register(db, body.email, body.password)
    token = create_access_token({"sub": user.email})
    return RegisterResponse(
        id=user.id,
        email=user.email,
        access_token=token,
        token_type="bearer",
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate and get a JWT token",
    dependencies=[Depends(auth_rate_limit)],
)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Validate credentials and issue a JWT access token."""
    return await auth_service.login(db, body.email, body.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh an expiring JWT token",
)
async def refresh(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Exchange a valid JWT for a fresh access token."""
    return await auth_service.refresh_token(db, token)


@router.get(
    "/gmail/url",
    response_model=GmailUrlResponse,
    summary="Get the Gmail OAuth consent URL",
)
async def gmail_oauth_url() -> GmailUrlResponse:
    """Return the Google OAuth consent URL for Gmail/Calendar scopes.

    No authentication required – the consent URL is not user-specific.
    """
    url = get_oauth_url()
    return GmailUrlResponse(url=url)


@router.post(
    "/gmail/callback",
    response_model=GmailCallbackResponse,
    summary="Exchange OAuth code for tokens (login or link)",
)
async def gmail_callback(
    body: GmailCallbackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> GmailCallbackResponse:
    """Exchange the Google OAuth authorization code.

    Works in two modes:
    - **Authenticated** (Authorization header present): links Gmail to the
      existing user account.
    - **Unauthenticated**: performs a login-via-Gmail flow – finds or creates
      a user by their Gmail address and returns a JWT.
    """
    # Try to extract the current user from the Authorization header.
    user: User | None = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ").strip()
        if token:
            try:
                payload = decode_token(token)
                email = payload.get("sub")
                if email:
                    from sqlalchemy import select
                    result = await db.execute(select(User).where(User.email == email))
                    user = result.scalars().first()
            except Exception:
                pass  # Token invalid/expired – fall through to unauthenticated flow.

    if user is not None:
        # Authenticated flow – link Gmail to existing account.
        result = await auth_service.handle_gmail_callback(db, user, body.code)
        return GmailCallbackResponse(status=result["status"], email=result["email"])

    # Unauthenticated flow – login / register via Gmail.
    result = await auth_service.handle_gmail_login(db, body.code)
    return GmailCallbackResponse(
        status=result["status"],
        email=result["email"],
        access_token=result.get("access_token"),
        token_type="bearer" if result.get("access_token") else None,
    )


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a password reset email",
    dependencies=[Depends(auth_rate_limit)],
)
async def forgot_password(
    body: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Request password reset. Always returns 202 to prevent email enumeration.

    If an account with the provided email exists, a password reset email
    with a time-limited token will be sent. For security reasons, this
    endpoint returns the same response regardless of whether the email
    exists in the system.
    """
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if user:
        # Generate reset token (short expiry: 15 minutes)
        reset_token = create_password_reset_token({"sub": user.email})
        # TODO: Send email with reset link
        # For now, just log it
        logger.info("Password reset requested for %s", body.email)

    # Always return 202 to prevent email enumeration attacks
    return {"message": "If an account exists, a reset email has been sent."}


@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password using token from email",
    dependencies=[Depends(auth_rate_limit)],
)
async def reset_password(
    body: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Reset password using token from email.

    Validates the reset token, ensures it is a valid password reset token
    (type='reset'), and updates the user's password with the new value.
    """
    try:
        payload = decode_token(body.token)
        if payload.get("type") != "reset":
            raise ValueError("Invalid token type")

        email = payload.get("sub")
        if not email:
            raise ValueError("Invalid token payload")

        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")

        user.hashed_password = hash_password(body.new_password)
        await db.commit()
        return {"message": "Password reset successfully"}
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
