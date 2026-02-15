"""Authentication API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, oauth2_scheme
from app.core.security import create_access_token
from app.integrations.gmail.oauth import get_oauth_url
from app.models.user import User
from app.schemas.auth import (
    GmailCallbackRequest,
    GmailCallbackResponse,
    GmailUrlResponse,
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.services import auth_service

router = APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account",
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
async def gmail_oauth_url(
    _user: User = Depends(get_current_user),
) -> GmailUrlResponse:
    """Return the Google OAuth consent URL for Gmail/Calendar scopes."""
    url = get_oauth_url()
    return GmailUrlResponse(url=url)


@router.post(
    "/gmail/callback",
    response_model=GmailCallbackResponse,
    summary="Exchange OAuth code for tokens",
)
async def gmail_callback(
    body: GmailCallbackRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> GmailCallbackResponse:
    """Exchange the Google OAuth authorization code and link the Gmail account."""
    result = await auth_service.handle_gmail_callback(db, user, body.code)
    return GmailCallbackResponse(status=result["status"], email=result["email"])
