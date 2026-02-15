"""API middleware package."""

from app.api.middleware.error_handler import register_exception_handlers
from app.api.middleware.rate_limit import rate_limit

__all__ = [
    "register_exception_handlers",
    "rate_limit",
]
