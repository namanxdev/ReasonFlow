"""API tests for authentication endpoints."""

from __future__ import annotations

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
        """Test successful login."""
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
        assert "refresh_token" in data
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
        """Test token refresh."""
        # First get a refresh token by logging in
        login_response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "test@example.com",
                "password": "testpassword123",
            },
        )
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token to get new access token
        response = await client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {refresh_token}"},
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
