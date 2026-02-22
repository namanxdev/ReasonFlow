"""HTML sanitization utilities."""

import bleach

# Allowed tags for email content
ALLOWED_TAGS = [
    "p", "br", "div", "span", "h1", "h2", "h3", "h4", "h5", "h6",
    "a", "b", "strong", "i", "em", "u", "strike", "blockquote",
    "ul", "ol", "li", "table", "thead", "tbody", "tr", "td", "th",
]

ALLOWED_ATTRIBUTES = {
    "*": ["class"],
    "a": ["href", "title"],
    "img": ["src", "alt", "title", "width", "height"],
}

ALLOWED_STYLES = []


def sanitize_html(html: str | None) -> str:
    """Sanitize HTML content, removing potentially dangerous tags/attributes."""
    if not html:
        return ""
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        styles=ALLOWED_STYLES,
        strip=True,
    )


def strip_html_tags(text: str | None) -> str:
    """Remove all HTML tags, returning plain text."""
    if not text:
        return ""
    return bleach.clean(text, tags=[], strip=True)
