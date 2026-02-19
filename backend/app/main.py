"""FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import close_redis
from app.schemas.health import HealthResponse
from app.services import health_service


def _validate_production_config() -> None:
    """Validate production configuration on startup.

    Raises:
        ValueError: If any required production configuration is missing or invalid.
    """
    settings.validate_production()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown."""
    # Startup
    if settings.is_production:
        _validate_production_config()
    yield
    # Shutdown
    await close_redis()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="ReasonFlow",
        description="Autonomous Inbox AI Agent powered by LangGraph + Gemini",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.APP_DEBUG else None,
        redoc_url="/redoc" if settings.APP_DEBUG else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health endpoint
    @app.get("/health", tags=["health"], response_model=HealthResponse)
    async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
        """Health check endpoint for monitoring system status."""
        health_data = await health_service.check_health(db)
        return health_data

    # Import and include routers (deferred to avoid circular imports)
    from app.api.middleware.error_handler import register_exception_handlers
    from app.api.router import api_router

    app.include_router(api_router, prefix="/api/v1")

    # Global exception handlers
    register_exception_handlers(app)

    return app


app = create_app()
