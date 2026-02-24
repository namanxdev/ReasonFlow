"""CSRF protection middleware.

Provides double-submit cookie pattern for CSRF protection.
State-changing requests must include a valid CSRF token in the
X-CSRF-Token header that matches the token in the csrf_token cookie.
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Constants
CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_TOKEN_EXPIRY_HOURS = 24
# Safe methods per RFC 7231 - these don't need CSRF protection
SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
# Paths that are exempt from CSRF protection (e.g., webhook endpoints)
EXEMPT_PATHS = frozenset({
    "/api/v1/auth/gmail/callback",  # OAuth callback doesn't need CSRF
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
})


def _generate_csrf_token() -> str:
    """Generate a new CSRF token.
    
    Returns:
        A random URL-safe token string
    """
    return secrets.token_urlsafe(32)


def _should_skip_csrf(request: Request) -> bool:
    """Check if CSRF check should be skipped for this request.
    
    Args:
        request: The incoming request
        
    Returns:
        True if CSRF check should be skipped
    """
    # Skip for safe methods
    if request.method in SAFE_METHODS:
        return True
    
    # Skip for exempt paths
    path = request.url.path
    if any(path.startswith(exempt) for exempt in EXEMPT_PATHS):
        return True
    
    return False


class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware for CSRF protection using double-submit cookie pattern.
    
    On each request:
    1. If no CSRF cookie exists, generate a new token and set it as a cookie
    2. For state-changing methods (POST, PUT, DELETE, PATCH):
       - Verify the X-CSRF-Token header matches the cookie value
       - If mismatch, return 403 Forbidden
    
    The frontend should:
    1. Read the csrf_token cookie
    2. Include it as the X-CSRF-Token header for all state-changing requests
    """

    async def dispatch(self, request: Request, call_next):
        """Process the request with CSRF protection."""
        
        # Get existing CSRF token from cookie or generate new one
        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        if not csrf_cookie:
            csrf_cookie = _generate_csrf_token()
        
        # Store token in request state for response handler
        request.state.csrf_token = csrf_cookie
        
        # Check if we need to validate CSRF token
        if not _should_skip_csrf(request):
            csrf_header = request.headers.get(CSRF_HEADER_NAME)
            
            if not csrf_header:
                logger.warning(
                    "CSRF token missing in header for %s %s",
                    request.method,
                    request.url.path
                )
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "CSRF token missing. Include X-CSRF-Token header.",
                        "code": "CSRF_TOKEN_MISSING"
                    }
                )
            
            if not hmac.compare_digest(csrf_cookie, csrf_header):
                logger.warning(
                    "CSRF token mismatch for %s %s",
                    request.method,
                    request.url.path
                )
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=403,
                    content={
                        "detail": "CSRF token invalid.",
                        "code": "CSRF_TOKEN_INVALID"
                    }
                )
        
        # Process the request
        response = await call_next(request)
        
        # Set/update CSRF cookie
        # Use SameSite=Strict to prevent cross-site requests from sending the cookie
        # Use HttpOnly=False so JavaScript can read it (needed for double-submit pattern)
        # Use Secure in production
        from app.core.config import settings
        
        cookie_value = request.state.csrf_token
        max_age = CSRF_TOKEN_EXPIRY_HOURS * 3600
        
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=cookie_value,
            max_age=max_age,
            httponly=False,  # JavaScript needs to read this
            secure=settings.is_production,
            samesite="strict",
            path="/",
        )
        
        return response


def get_csrf_token(request: Request) -> str:
    """Get the current CSRF token for the request.
    
    This can be used by endpoints that need to return the token
    to the frontend (e.g., in HTML forms).
    
    Args:
        request: The current request
        
    Returns:
        The current CSRF token
    """
    return getattr(request.state, "csrf_token", "")
