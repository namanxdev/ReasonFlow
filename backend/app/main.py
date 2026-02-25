"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
import sys
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.middleware.csrf import CSRFMiddleware
from app.api.middleware.idempotency import IdempotencyMiddleware
from app.api.middleware.request_id import RequestIdMiddleware
from app.core.config import settings
from app.core.database import get_db
from app.core.logging import setup_logging
from app.core.task_tracker import TaskTracker, get_task_tracker
from app.schemas.health import HealthResponse
from app.services import health_service

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response


def _validate_production_config() -> None:
    """Validate production configuration on startup.

    Raises:
        ValueError: If any required production configuration is missing or invalid.
        SystemExit: If validation fails, exits with code 1 to prevent startup.
    """
    try:
        settings.validate_production()
    except ValueError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.critical("CRITICAL CONFIGURATION ERROR: %s", e)
        print(f"\n{'=' * 60}", file=sys.stderr)
        print("CRITICAL CONFIGURATION ERROR - Application Startup Aborted", file=sys.stderr)
        print(f"{'=' * 60}\n", file=sys.stderr)
        print(e, file=sys.stderr)
        print(f"\n{'=' * 60}", file=sys.stderr)
        print("Set a secure JWT_SECRET_KEY to start the application.", file=sys.stderr)
        print(f"{'=' * 60}\n", file=sys.stderr)
        sys.exit(1)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown."""
    # Startup
    setup_logging()
    
    # Initialize task tracker for graceful shutdown
    tracker = get_task_tracker()
    app.state.task_tracker = tracker
    
    if settings.is_production:
        _validate_production_config()

    from app.services.scheduler import start_scheduler
    start_scheduler()

    logger.info("Application startup complete")
    yield

    # Shutdown - wait for background tasks to complete
    from app.services.scheduler import stop_scheduler
    await stop_scheduler()
    logger.info("Application shutdown initiated, waiting for background tasks...")
    tracker.request_shutdown()
    completed = await tracker.wait_for_completion(timeout=30.0)
    if not completed:
        logger.warning("Some background tasks did not complete gracefully")
    logger.info("Application shutdown complete")


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

    # Request ID middleware (added first to capture ID for all subsequent middleware)
    app.add_middleware(RequestIdMiddleware)

    # CSRF protection middleware (before auth, after request ID)
    app.add_middleware(CSRFMiddleware)

    # Security headers middleware (added before CORS)
    app.add_middleware(SecurityHeadersMiddleware)

    # Idempotency middleware
    app.add_middleware(IdempotencyMiddleware)

    # CORS - allow credentials for httpOnly cookies (SEC-3 fix)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With", "X-CSRF-Token"],
        expose_headers=["X-Request-ID"],
    )

    # Health endpoint
    @app.get("/health", tags=["health"], response_model=HealthResponse)
    async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
        """Health check endpoint for monitoring system status."""
        health_data = await health_service.check_health(db)
        return health_data

    # Import and include routers (deferred to avoid circular imports)
    from app.api.middleware.error_handler import register_exception_handlers
    from app.api.router import api_router, ws_router

    app.include_router(api_router, prefix="/api/v1")
    app.include_router(ws_router, prefix="/api/v1")

    # Global exception handlers
    register_exception_handlers(app)

    return app


app = create_app()
