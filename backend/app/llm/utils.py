"""LLM utility functions."""


def truncate_text(text: str, max_chars: int = 4000, suffix: str = "...") -> str:
    """Truncate text to max_chars, adding suffix if truncated."""
    if not text or len(text) <= max_chars:
        return text
    return text[: max_chars - len(suffix)] + suffix
