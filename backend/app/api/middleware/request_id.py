"""Request ID middleware for distributed tracing."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import request_id_var

if TYPE_CHECKING:
    from fastapi import Request, Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware to generate and propagate request IDs for distributed tracing.

    This middleware ensures each request has a unique identifier that can be
    used for tracing requests across the system and in logs.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add request ID to response headers.

        Args:
            request: The incoming FastAPI request.
            call_next: The next middleware/endpoint in the chain.

        Returns:
            The response with X-Request-ID header added.
        """
        # Get request ID from header or generate new one
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # Store in request state for access in endpoints
        request.state.request_id = request_id

        # Set request ID in context variable for logging correlation
        token = request_id_var.set(request_id)

        try:
            # Process request
            response = await call_next(request)
        finally:
            # Reset context variable after request completes
            request_id_var.reset(token)

        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id

        return response


def get_request_id(request: Request) -> str:
    """Get the request ID from the request state.

    Args:
        request: The FastAPI request object.

    Returns:
        The request ID string, or "unknown" if not set.
    """
    return getattr(request.state, "request_id", "unknown")
