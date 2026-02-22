"""Global exception handler middleware."""

from __future__ import annotations

import logging
import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, OperationalError, TimeoutError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.integrations.gmail.exceptions import GmailAPIError, GmailAuthError, GmailRateLimitError
from app.schemas.common import ErrorResponse

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach global exception handlers to the FastAPI application."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Pass-through for FastAPI/Starlette HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content=ErrorResponse(
                detail=str(exc.detail),
                code=f"HTTP_{exc.status_code}",
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Convert Pydantic validation errors to a 422 response."""
        errors = exc.errors()
        detail = "; ".join(
            f"{'.'.join(str(loc) for loc in e['loc'])}: {e['msg']}" for e in errors
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponse(
                detail=detail,
                code="VALIDATION_ERROR",
                extra={"errors": errors},
            ).model_dump(),
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request, exc: ValueError
    ) -> JSONResponse:
        """Map ValueError to 400 Bad Request."""
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                detail=str(exc),
                code="BAD_REQUEST",
            ).model_dump(),
        )

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(
        request: Request, exc: IntegrityError
    ) -> JSONResponse:
        """Handle SQLAlchemy IntegrityError (constraint violations, duplicate keys)."""
        logger.warning("IntegrityError on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponse(
                detail="Resource already exists or constraint violated",
                code="INTEGRITY_ERROR",
            ).model_dump(),
        )

    @app.exception_handler(OperationalError)
    async def operational_error_handler(
        request: Request, exc: OperationalError
    ) -> JSONResponse:
        """Handle SQLAlchemy OperationalError (connection errors)."""
        logger.error(
            "Database connection error on %s %s: %s", request.method, request.url.path, exc
        )
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ErrorResponse(
                detail="Database connection error. Please try again later.",
                code="DB_CONNECTION_ERROR",
            ).model_dump(),
        )

    @app.exception_handler(TimeoutError)
    async def timeout_error_handler(
        request: Request, exc: TimeoutError
    ) -> JSONResponse:
        """Handle SQLAlchemy TimeoutError (query timeouts)."""
        logger.error("Database timeout on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content=ErrorResponse(
                detail="Database query timed out. Please try again.",
                code="DB_TIMEOUT",
            ).model_dump(),
        )

    @app.exception_handler(GmailAuthError)
    async def gmail_auth_error_handler(
        request: Request, exc: GmailAuthError
    ) -> JSONResponse:
        """Handle Gmail OAuth authentication errors."""
        logger.warning("Gmail auth error on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(
                detail="Gmail authentication failed. Please reconnect your account.",
                code="GMAIL_AUTH_ERROR",
            ).model_dump(),
        )

    @app.exception_handler(GmailRateLimitError)
    async def gmail_rate_limit_handler(
        request: Request, exc: GmailRateLimitError
    ) -> JSONResponse:
        """Handle Gmail API rate limit errors."""
        headers = {}
        if exc.retry_after:
            headers["Retry-After"] = str(exc.retry_after)
        logger.warning(
            "Gmail rate limit on %s %s, retry_after=%s",
            request.method,
            request.url.path,
            exc.retry_after,
        )
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=ErrorResponse(
                detail="Gmail API rate limit exceeded. Please try again later.",
                code="GMAIL_RATE_LIMIT",
            ).model_dump(),
            headers=headers,
        )

    @app.exception_handler(GmailAPIError)
    async def gmail_api_error_handler(
        request: Request, exc: GmailAPIError
    ) -> JSONResponse:
        """Handle general Gmail API errors."""
        logger.error("Gmail API error on %s %s: %s", request.method, request.url.path, exc)
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=ErrorResponse(
                detail="Gmail API error. Please try again later.",
                code="GMAIL_API_ERROR",
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all for unexpected errors — log the traceback and return 500."""
        logger.error(
            "Unhandled exception on %s %s: %s\n%s",
            request.method,
            request.url.path,
            exc,
            traceback.format_exc(),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                detail="Internal server error",
                code="INTERNAL_ERROR",
            ).model_dump(),
        )
