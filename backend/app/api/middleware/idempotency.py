"""Idempotency middleware for API requests."""

from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Middleware to handle Idempotency-Key headers for safe request retries.

    This middleware extracts the Idempotency-Key header from incoming requests
    and stores it in the request state for handlers to use. It also returns
    the idempotency key in the response headers when provided.
    """

    async def dispatch(self, request: Request, call_next):
        """Process the request and handle idempotency key.

        Args:
            request: The incoming FastAPI request.
            call_next: The next middleware/handler in the chain.

        Returns:
            The response with idempotency header if provided.
        """
        # Check for Idempotency-Key header
        idempotency_key = request.headers.get("Idempotency-Key")

        if idempotency_key:
            # Store in request state for handlers to use
            request.state.idempotency_key = idempotency_key

        response = await call_next(request)

        # If idempotency key was used, return it in response
        if idempotency_key:
            response.headers["Idempotency-Key"] = idempotency_key

        return response
