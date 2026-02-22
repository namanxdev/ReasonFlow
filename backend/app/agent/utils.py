"""Utility functions for agent nodes."""


def truncate_email_body(body: str, max_chars: int = 4000) -> str:
    """Truncate email body to fit within LLM context limits.

    Args:
        body: The email body text to truncate.
        max_chars: Maximum character limit (default: 4000).

    Returns:
        Truncated text with indicator if truncation occurred.
    """
    if len(body) <= max_chars:
        return body
    return body[:max_chars] + "\n\n[Content truncated due to length...]"
