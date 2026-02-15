"""Authentication and cryptographic utilities."""

from __future__ import annotations

import base64
import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet, InvalidToken
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

REFRESH_TOKEN_EXPIRE_DAYS: int = 7


def hash_password(password: str) -> str:
    """Return a bcrypt hash of *password*."""
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Return ``True`` if *plain* matches the bcrypt *hashed* value."""
    return _pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT tokens
# ---------------------------------------------------------------------------


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token."""
    to_encode = data.copy()
    expire = datetime.now(UTC) + (
        expires_delta
        if expires_delta is not None
        else timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
    )
    to_encode["exp"] = expire
    to_encode["type"] = "access"
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a signed JWT refresh token with a 7-day lifetime."""
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode["type"] = "refresh"
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token, raising ValueError on failure."""
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except ExpiredSignatureError as exc:
        raise ValueError("Token has expired") from exc
    except JWTError as exc:
        raise ValueError("Invalid token") from exc
    return payload


# ---------------------------------------------------------------------------
# Fernet (OAuth token encryption)
# ---------------------------------------------------------------------------


def _derive_fernet_key() -> bytes:
    """Derive a Fernet key from JWT_SECRET_KEY via SHA-256."""
    digest = hashlib.sha256(settings.JWT_SECRET_KEY.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def _get_fernet() -> Fernet:
    return Fernet(_derive_fernet_key())


def encrypt_oauth_token(token: str) -> str:
    """Encrypt *token* using Fernet symmetric encryption."""
    return _get_fernet().encrypt(token.encode()).decode()


def decrypt_oauth_token(encrypted: str) -> str:
    """Decrypt a Fernet-encrypted OAuth token, raising ValueError on failure."""
    try:
        return _get_fernet().decrypt(encrypted.encode()).decode()
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt OAuth token: invalid or corrupted data") from exc
