"""API tests for authentication endpoints."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


@pytest.mark.asyncio
class TestAuthEndpoints:
    """Test authentication API endpoints."""

    async def test_register_success(self, client):
        """Test successful user registration."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    async def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    async def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client):
        """Test registration with short password."""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "short",
            },
        )
        assert response.status_code == 422

    async def test_login_success(self, client, test_user):
        """Test successful login.

        The refresh token is set as an httpOnly cookie; the response body
        contains only the access token (TokenResponse, no refresh_token field).
        """
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" not in data  # refresh_token is in httpOnly cookie
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    async def test_refresh_token_success(self, client, test_user, auth_token):
        """Test token refresh using the httpOnly cookie set at login."""
        # Log in — the refresh token is delivered as an httpOnly cookie.
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        assert login_response.status_code == 200
        refresh_token_cookie = login_response.cookies.get("refresh_token")

        # Use refresh token cookie to get new access token.
        response = await client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": refresh_token_cookie} if refresh_token_cookie else {},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    async def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token."""
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    async def test_forgot_password_returns_202(self, client, test_user):
        """Test forgot password returns 202."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "test@example.com"},
        )
        assert response.status_code == 202

    async def test_forgot_password_nonexistent_email(self, client):
        """Test forgot password with non-existent email still returns 202."""
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"},
        )
        assert response.status_code == 202


@pytest.mark.asyncio
class TestGmailCallback:
    """Test Gmail OAuth callback endpoint."""

    async def test_gmail_callback_unauthenticated_sets_refresh_cookie(self, client):
        """Unauthenticated Gmail login must set an httpOnly refresh_token cookie."""
        with patch(
            "app.api.routes.auth.auth_service.handle_gmail_login",
            new=AsyncMock(return_value={
                "status": "logged_in",
                "email": "gmailuser@gmail.com",
                "access_token": "gmail-access-token",
            }),
        ):
            response = await client.post(
                "/api/v1/auth/gmail/callback",
                json={"code": "valid-oauth-code"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "gmail-access-token"
        assert data["email"] == "gmailuser@gmail.com"
        # Refresh token must be delivered as an httpOnly cookie, not in body
        assert "refresh_token" not in data
        assert "refresh_token" in response.cookies

    async def test_gmail_callback_unauthenticated_no_cookie_when_no_access_token(
        self, client
    ):
        """If handle_gmail_login returns no access_token, no cookie is set."""
        with patch(
            "app.api.routes.auth.auth_service.handle_gmail_login",
            new=AsyncMock(return_value={
                "status": "error",
                "email": "",
            }),
        ):
            response = await client.post(
                "/api/v1/auth/gmail/callback",
                json={"code": "valid-oauth-code"},
            )

        assert response.status_code == 200
        assert "refresh_token" not in response.cookies

    async def test_gmail_callback_authenticated_links_account_no_cookie(
        self, client, test_user, auth_token
    ):
        """Authenticated flow (linking) should NOT set a refresh cookie."""
        with patch(
            "app.api.routes.auth.auth_service.handle_gmail_callback",
            new=AsyncMock(return_value={"status": "connected", "email": "gmailuser@gmail.com"}),
        ):
            response = await client.post(
                "/api/v1/auth/gmail/callback",
                json={"code": "valid-oauth-code"},
                headers={"Authorization": f"Bearer {auth_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "connected"
        # Linking flow must not issue a new refresh cookie
        assert "refresh_token" not in response.cookies

    async def test_gmail_callback_refresh_cookie_is_valid_jwt(self, client):
        """The refresh_token cookie set by Gmail login must be a decodable JWT."""
        from app.core.security import decode_token

        with patch(
            "app.api.routes.auth.auth_service.handle_gmail_login",
            new=AsyncMock(return_value={
                "status": "logged_in",
                "email": "gmailuser@gmail.com",
                "access_token": "gmail-access-token",
            }),
        ):
            response = await client.post(
                "/api/v1/auth/gmail/callback",
                json={"code": "valid-oauth-code"},
            )

        assert response.status_code == 200
        cookie_value = response.cookies.get("refresh_token")
        assert cookie_value is not None
        payload = decode_token(cookie_value)
        assert payload["sub"] == "gmailuser@gmail.com"
        assert payload["type"] == "refresh"


@pytest.mark.asyncio
class TestProtectedEndpoints:
    """Test that protected endpoints require authentication."""

    async def test_emails_list_requires_auth(self, client):
        """Test that emails endpoint requires authentication."""
        response = await client.get("/api/v1/emails")
        assert response.status_code == 401

    async def test_crm_contacts_requires_auth(self, client):
        """Test that CRM contacts endpoint requires authentication."""
        response = await client.get("/api/v1/crm/contacts")
        assert response.status_code == 401

    async def test_metrics_requires_auth(self, client):
        """Test that metrics endpoint requires authentication."""
        response = await client.get("/api/v1/metrics")
        assert response.status_code == 401
