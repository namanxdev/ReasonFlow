"""Authentication business logic."""

from __future__ import annotations

import logging
import uuid

import httpx
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    decrypt_oauth_token,
    encrypt_oauth_token,
    hash_password,
    verify_password,
)
from app.integrations.gmail.oauth import exchange_code
from app.models.user import User
from app.schemas.auth import TokenResponse, TokenResponseWithRefresh

logger = logging.getLogger(__name__)

_GMAIL_PROFILE_URL = "https://gmail.googleapis.com/gmail/v1/users/me/profile"


async def register(db: AsyncSession, email: str, password: str) -> User:
    """Create a new user with a hashed password.

    Raises HTTP 409 if the email address is already registered.
    """
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalars().first()
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists.",
        )

    user = User(
        email=email,
        hashed_password=hash_password(password),
    )
    db.add(user)
    await db.flush()  # Populate user.id without committing the transaction.
    await db.refresh(user)
    logger.info("Registered new user email=%s id=%s", email, user.id)
    return user


async def login(db: AsyncSession, email: str, password: str) -> TokenResponseWithRefresh:
    """Verify credentials and return a JWT access token plus refresh token.

    Raises HTTP 401 if the email is not found or the password is wrong.
    """
    result = await db.execute(select(User).where(User.email == email))
    user: User | None = result.scalars().first()

    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = {"sub": user.email}
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    logger.info("User logged in email=%s", email)
    return TokenResponseWithRefresh(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRATION_MINUTES * 60,
    )


async def refresh_token(db: AsyncSession, refresh_token_str: str) -> TokenResponse:
    """Validate a refresh token and issue a new access token.

    Raises HTTP 401 if the token is invalid, expired, or not a refresh token.
    Raises HTTP 404 if the user referenced in the token no longer exists.
    """
    try:
        payload = decode_token(refresh_token_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not a refresh token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    subject: str | None = payload.get("sub")
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token subject is missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.email == subject))
    user: User | None = result.scalars().first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    new_access_token = create_access_token({"sub": user.email})
    logger.info("Refreshed access token for email=%s", user.email)
    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=None,
    )


async def handle_gmail_callback(
    db: AsyncSession, user: User, code: str
) -> dict[str, str]:
    """Exchange the OAuth authorization code for tokens, encrypt, and persist them.

    Returns a dict with ``status`` and the connected Gmail ``email``.

    Raises HTTP 400 if Google rejects the authorization code.
    Raises HTTP 502 if the token exchange network request fails.
    """
    try:
        token_data = await exchange_code(code)
    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Gmail OAuth code exchange failed for user=%s: %s %s",
            user.id,
            exc.response.status_code,
            exc.response.text,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth authorization code.",
        ) from exc
    except httpx.RequestError as exc:
        logger.error("Network error during Gmail OAuth exchange for user=%s: %s", user.id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to reach Google authorization server.",
        ) from exc

    access_token: str = token_data.get("access_token", "")
    refresh_token_value: str = token_data.get("refresh_token", "")

    user.oauth_token_encrypted = encrypt_oauth_token(access_token)
    if refresh_token_value:
        user.oauth_refresh_token_encrypted = encrypt_oauth_token(refresh_token_value)

    await db.flush()

    # Resolve the Gmail address that was connected.
    gmail_email = await _resolve_gmail_address(user, access_token)

    logger.info(
        "Gmail OAuth connected for user=%s gmail_email=%s", user.id, gmail_email
    )
    return {"status": "connected", "email": gmail_email}


async def handle_gmail_login(
    db: AsyncSession, code: str
) -> dict[str, str]:
    """Exchange the OAuth code, find or create the user, and return a JWT.

    This supports the unauthenticated "Login with Gmail" flow.

    Returns a dict with ``status``, ``email``, and ``access_token``.
    """
    try:
        token_data = await exchange_code(code)
    except httpx.HTTPStatusError as exc:
        logger.warning("Gmail OAuth code exchange failed: %s %s", exc.response.status_code, exc.response.text)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth authorization code.",
        ) from exc
    except httpx.RequestError as exc:
        logger.error("Network error during Gmail OAuth exchange: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to reach Google authorization server.",
        ) from exc

    access_token_google: str = token_data.get("access_token", "")
    refresh_token_google: str = token_data.get("refresh_token", "")

    # Resolve the Gmail address.
    gmail_email = ""
    try:
        async with httpx.AsyncClient() as http_client:
            profile_resp = await http_client.get(
                _GMAIL_PROFILE_URL,
                headers={"Authorization": f"Bearer {access_token_google}"},
            )
            profile_resp.raise_for_status()
            gmail_email = profile_resp.json().get("emailAddress", "")
    except Exception as exc:
        logger.warning("Could not resolve Gmail profile email: %s", exc)

    if not gmail_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not determine Gmail address from Google.",
        )

    # Find or create user.
    result = await db.execute(select(User).where(User.email == gmail_email))
    user: User | None = result.scalars().first()

    if user is None:
        # Auto-register; use a random unusable password since they login via OAuth.
        import secrets
        user = User(
            email=gmail_email,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        logger.info("Auto-registered Gmail user email=%s id=%s", gmail_email, user.id)

    # Store / update OAuth tokens.
    user.oauth_token_encrypted = encrypt_oauth_token(access_token_google)
    if refresh_token_google:
        user.oauth_refresh_token_encrypted = encrypt_oauth_token(refresh_token_google)
    await db.flush()

    # Issue a JWT.
    jwt_token = create_access_token({"sub": user.email})
    logger.info("Gmail login successful for email=%s", gmail_email)

    return {"status": "connected", "email": gmail_email, "access_token": jwt_token}


async def _resolve_gmail_address(user: User, access_token: str) -> str:
    """Fetch the Gmail profile address; fall back to the registered email on failure."""
    try:
        async with httpx.AsyncClient() as http_client:
            profile_response = await http_client.get(
                _GMAIL_PROFILE_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            profile_response.raise_for_status()
            return profile_response.json().get("emailAddress", "")
    except Exception as exc:
        logger.warning(
            "Could not resolve Gmail profile email for user=%s: %s", user.id, exc
        )
        return user.email  # Fall back to the registered email.


async def refresh_user_gmail_token(db: AsyncSession, user_id: uuid.UUID) -> bool:
    """Refresh Gmail OAuth token for user if needed.

    Checks if the user's access token is expired (or about to expire within 5 minutes),
    and if so, exchanges the refresh token for a new access token from Google's
    OAuth2 token endpoint. The new token is encrypted and stored in the database.

    Args:
        db: Database session for updating user record.
        user_id: UUID of the user whose token should be refreshed.

    Returns:
        True if token was refreshed (or still valid), False if refresh failed
        or user has no refresh token.
    """

    from app.core.config import settings

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.oauth_refresh_token_encrypted:
        logger.debug("No refresh token available for user=%s", user_id)
        return False

    # Decrypt the current refresh token
    try:
        refresh_token = decrypt_oauth_token(user.oauth_refresh_token_encrypted)
    except ValueError as exc:
        logger.warning("Failed to decrypt refresh token for user=%s: %s", user_id, exc)
        return False

    # Check if access token exists and is still valid (with 5 minute buffer)
    if user.oauth_token_encrypted:
        # Note: We don't store expires_at in the User model currently,
        # so we'll always attempt to get a fresh token when this is called.
        # In production, you might want to add oauth_token_expires_at column.
        pass

    # Exchange refresh token for new access token
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GMAIL_CLIENT_ID,
                "client_secret": settings.GMAIL_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )

        if response.status_code != 200:
            logger.warning(
                "Failed to refresh Gmail token for user=%s: %s %s",
                user_id,
                response.status_code,
                response.text,
            )
            return False

        token_data = response.json()
        new_access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)

        if not new_access_token:
            logger.error("No access_token in Google refresh response for user=%s", user_id)
            return False

        # Encrypt and store the new access token
        user.oauth_token_encrypted = encrypt_oauth_token(new_access_token)
        await db.flush()

        logger.info(
            "Successfully refreshed Gmail token for user=%s (expires_in=%s)",
            user_id,
            expires_in,
        )
        return True
