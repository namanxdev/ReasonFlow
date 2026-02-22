"""Gmail integration exceptions."""

from __future__ import annotations


class GmailAuthError(Exception):
    """Raised when Gmail OAuth fails."""
    pass


class GmailRateLimitError(Exception):
    """Raised when Gmail API rate limit is hit."""

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class GmailAPIError(Exception):
    """Raised when Gmail API returns an error."""
    pass
