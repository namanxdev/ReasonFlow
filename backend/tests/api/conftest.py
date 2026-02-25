"""Pytest fixtures for API tests."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.database import Base, async_engine, async_session_factory
from app.core.security import create_access_token, hash_password
from app.main import create_app
from app.models.user import User

# Override settings for testing
settings.DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/reasonflow_test"
settings.JWT_SECRET_KEY = "test-secret-key-for-testing-only"
settings.ENCRYPTION_KEY = "test-encryption-key-for-testing"
settings.GEMINI_API_KEY = "test-gemini-key"


@pytest_asyncio.fixture(scope="session")
async def setup_database() -> AsyncGenerator[None, None]:
    """Create test database tables."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(setup_database) -> AsyncGenerator[Any, None]:
    """Create a fresh database session for each test."""
    async with async_session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def app(setup_database):
    """Create application instance."""
    return create_app()


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP client for testing."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def test_user(db_session) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        hashed_password=hash_password("testpassword123"),
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_token(test_user) -> str:
    """Generate auth token for test user."""
    return create_access_token({"sub": test_user.email})


@pytest_asyncio.fixture
async def auth_client(client, auth_token) -> AsyncClient:
    """Create authenticated HTTP client."""
    client.headers["Authorization"] = f"Bearer {auth_token}"
    return client
