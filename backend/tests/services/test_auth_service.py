"""Unit tests for auth_service module."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.user import User
from app.schemas.auth import TokenResponse, TokenResponseWithRefresh
from tests.services.conftest import make_user

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_scalar_result(value):
    """Return a mock that behaves like scalars().first() returning *value*."""
    scalars_mock = MagicMock()
    scalars_mock.first.return_value = value
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    result_mock.scalar_one_or_none.return_value = value
    return result_mock


# ---------------------------------------------------------------------------
# register()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_creates_user_with_hashed_password(mock_db):
    """register() should add a new User with a bcrypt-hashed password."""
    from app.services.auth_service import register

    mock_db.execute = AsyncMock(return_value=_make_scalar_result(None))

    with patch("app.services.auth_service.hash_password", return_value="hashed_pw") as mock_hash:
        await register(mock_db, "new@example.com", "secret123")

    mock_hash.assert_called_once_with("secret123")
    mock_db.add.assert_called_once()
    added_user: User = mock_db.add.call_args[0][0]
    assert added_user.email == "new@example.com"
    assert added_user.hashed_password == "hashed_pw"
    mock_db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_register_raises_409_if_email_exists(mock_db):
    """register() should raise HTTP 409 when the email is already taken."""
    from fastapi import HTTPException

    from app.services.auth_service import register

    existing_user = make_user(email="dupe@example.com")
    mock_db.execute = AsyncMock(return_value=_make_scalar_result(existing_user))

    with pytest.raises(HTTPException) as exc_info:
        await register(mock_db, "dupe@example.com", "password123")

    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# login()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_returns_token_for_valid_credentials(mock_db):
    """login() should return a TokenResponseWithRefresh for correct email/password."""
    from app.services.auth_service import login

    user = make_user(email="user@example.com", hashed_password="hashed_pw")
    mock_db.execute = AsyncMock(return_value=_make_scalar_result(user))

    with (
        patch("app.services.auth_service.verify_password", return_value=True),
        patch("app.services.auth_service.create_access_token", return_value="access.token"),
        patch("app.services.auth_service.create_refresh_token", return_value="refresh.token"),
    ):
        response = await login(mock_db, "user@example.com", "correct_pw")

    assert isinstance(response, TokenResponseWithRefresh)
    assert isinstance(response, TokenResponse)  # Subclass — still a TokenResponse.
    assert response.access_token == "access.token"
    assert response.refresh_token == "refresh.token"
    assert response.token_type == "bearer"
    assert response.expires_in is not None and response.expires_in > 0


@pytest.mark.asyncio
async def test_login_raises_401_for_wrong_password(mock_db):
    """login() should raise HTTP 401 when the password does not match."""
    from fastapi import HTTPException

    from app.services.auth_service import login

    user = make_user(email="user@example.com", hashed_password="hashed_pw")
    mock_db.execute = AsyncMock(return_value=_make_scalar_result(user))

    with patch("app.services.auth_service.verify_password", return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await login(mock_db, "user@example.com", "wrong_pw")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_login_raises_401_for_unknown_email(mock_db):
    """login() should raise HTTP 401 when the email is not found."""
    from fastapi import HTTPException

    from app.services.auth_service import login

    mock_db.execute = AsyncMock(return_value=_make_scalar_result(None))

    with pytest.raises(HTTPException) as exc_info:
        await login(mock_db, "ghost@example.com", "any_pw")

    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# refresh_token()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_token_returns_new_access_token(mock_db):
    """refresh_token() should return a new TokenResponse for a valid refresh token."""
    from app.services.auth_service import refresh_token

    user = make_user(email="user@example.com")
    mock_db.execute = AsyncMock(return_value=_make_scalar_result(user))

    with (
        patch(
            "app.services.auth_service.decode_token",
            return_value={"sub": "user@example.com", "type": "refresh"},
        ),
        patch("app.services.auth_service.create_access_token", return_value="new.token"),
    ):
        response = await refresh_token(mock_db, "some.refresh.token")

    assert isinstance(response, TokenResponse)
    assert response.access_token == "new.token"
    assert response.expires_in is None  # Refresh responses omit expires_in.


@pytest.mark.asyncio
async def test_refresh_token_raises_401_for_expired_token(mock_db):
    """refresh_token() should raise HTTP 401 when the token is expired or invalid."""
    from fastapi import HTTPException

    from app.services.auth_service import refresh_token

    with patch(
        "app.services.auth_service.decode_token",
        side_effect=ValueError("Token has expired"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(mock_db, "expired.token")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_raises_401_if_not_refresh_type(mock_db):
    """refresh_token() should reject access tokens passed as refresh tokens."""
    from fastapi import HTTPException

    from app.services.auth_service import refresh_token

    with patch(
        "app.services.auth_service.decode_token",
        return_value={"sub": "user@example.com", "type": "access"},
    ):
        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(mock_db, "access.token")

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_raises_404_if_user_missing(mock_db):
    """refresh_token() should raise HTTP 404 if the referenced user no longer exists."""
    from fastapi import HTTPException

    from app.services.auth_service import refresh_token

    mock_db.execute = AsyncMock(return_value=_make_scalar_result(None))

    with patch(
        "app.services.auth_service.decode_token",
        return_value={"sub": "gone@example.com", "type": "refresh"},
    ):
        with pytest.raises(HTTPException) as exc_info:
            await refresh_token(mock_db, "valid.refresh.token")

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# handle_gmail_callback()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_gmail_callback_stores_encrypted_tokens(mock_db):
    """handle_gmail_callback() should encrypt and persist OAuth tokens."""
    from app.services.auth_service import handle_gmail_callback

    user = make_user()
    token_data = {
        "access_token": "gmail_access",
        "refresh_token": "gmail_refresh",
    }

    class FakeResponse:
        status_code = 200

        def json(self):
            return {"emailAddress": "user@gmail.com"}

        def raise_for_status(self):
            pass

    fake_http_client = AsyncMock()
    fake_http_client.__aenter__ = AsyncMock(return_value=fake_http_client)
    fake_http_client.__aexit__ = AsyncMock(return_value=False)
    fake_http_client.get = AsyncMock(return_value=FakeResponse())

    with (
        patch("app.services.auth_service.exchange_code", AsyncMock(return_value=token_data)),
        patch("app.services.auth_service.encrypt_oauth_token", side_effect=lambda t: f"enc:{t}"),
        patch("app.services.auth_service.httpx") as mock_httpx,
    ):
        mock_httpx.AsyncClient.return_value = fake_http_client
        result = await handle_gmail_callback(mock_db, user, "auth-code")

    assert result["status"] == "connected"
    assert user.oauth_token_encrypted == "enc:gmail_access"
    assert user.oauth_refresh_token_encrypted == "enc:gmail_refresh"
    mock_db.flush.assert_awaited()


@pytest.mark.asyncio
async def test_handle_gmail_callback_raises_400_on_bad_code(mock_db):
    """handle_gmail_callback() should raise HTTP 400 when Google rejects the code."""
    import httpx as real_httpx
    from fastapi import HTTPException

    from app.services.auth_service import handle_gmail_callback

    user = make_user()
    fake_response = MagicMock()
    fake_response.status_code = 400
    fake_response.text = "bad_grant"

    with patch(
        "app.services.auth_service.exchange_code",
        side_effect=real_httpx.HTTPStatusError(
            "bad grant", request=MagicMock(), response=fake_response
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await handle_gmail_callback(mock_db, user, "bad-code")

    assert exc_info.value.status_code == 400


# -----------------------------------------------------------------------------
# refresh_user_gmail_token()
# -----------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_user_gmail_token_success(mock_db):
    """refresh_user_gmail_token() should refresh and store new access token."""
    from app.services.auth_service import refresh_user_gmail_token

    user = make_user()
    user.oauth_refresh_token_encrypted = "enc_refresh_token"
    mock_db.execute = AsyncMock(return_value=_make_scalar_result(user))

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "access_token": "new_access_token",
        "expires_in": 3600,
    }

    with (
        patch(
            "app.services.auth_service.decrypt_oauth_token",
            return_value="decrypted_refresh_token",
        ),
        patch(
            "app.services.auth_service.encrypt_oauth_token",
            return_value="enc_new_access_token",
        ),
        patch("httpx.AsyncClient.post", AsyncMock(return_value=fake_response)),
    ):
        result = await refresh_user_gmail_token(mock_db, user.id)

    assert result is True
    assert user.oauth_token_encrypted == "enc_new_access_token"
    mock_db.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_refresh_user_gmail_token_no_user(mock_db):
    """refresh_user_gmail_token() should return False if user not found."""
    from app.services.auth_service import refresh_user_gmail_token

    mock_db.execute = AsyncMock(return_value=_make_scalar_result(None))

    result = await refresh_user_gmail_token(mock_db, uuid.uuid4())

    assert result is False


@pytest.mark.asyncio
async def test_refresh_user_gmail_token_no_refresh_token(mock_db):
    """refresh_user_gmail_token() should return False if no refresh token."""
    from app.services.auth_service import refresh_user_gmail_token

    user = make_user()
    # No oauth_refresh_token_encrypted set
    mock_db.execute = AsyncMock(return_value=_make_scalar_result(user))

    result = await refresh_user_gmail_token(mock_db, user.id)

    assert result is False


@pytest.mark.asyncio
async def test_refresh_user_gmail_token_google_error(mock_db):
    """refresh_user_gmail_token() should return False on Google API error."""
    from app.services.auth_service import refresh_user_gmail_token

    user = make_user()
    user.oauth_refresh_token_encrypted = "enc_refresh_token"
    mock_db.execute = AsyncMock(return_value=_make_scalar_result(user))

    fake_response = MagicMock()
    fake_response.status_code = 400
    fake_response.text = "invalid_grant"

    with (
        patch(
            "app.services.auth_service.decrypt_oauth_token",
            return_value="decrypted_refresh_token",
        ),
        patch("httpx.AsyncClient.post", AsyncMock(return_value=fake_response)),
    ):
        result = await refresh_user_gmail_token(mock_db, user.id)

    assert result is False


@pytest.mark.asyncio
async def test_refresh_user_gmail_token_decrypt_failure(mock_db):
    """refresh_user_gmail_token() should return False if decrypt fails."""
    from app.services.auth_service import refresh_user_gmail_token

    user = make_user()
    user.oauth_refresh_token_encrypted = "invalid_encrypted_token"
    mock_db.execute = AsyncMock(return_value=_make_scalar_result(user))

    with patch(
        "app.services.auth_service.decrypt_oauth_token",
        side_effect=ValueError("Invalid token"),
    ):
        result = await refresh_user_gmail_token(mock_db, user.id)

    assert result is False
