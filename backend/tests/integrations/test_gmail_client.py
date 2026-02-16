"""Unit tests for Gmail client body-decoding helpers."""

from __future__ import annotations

import base64

from app.integrations.gmail.client import _decode_body, _strip_html

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _b64(text: str) -> str:
    """Base64url-encode a string the same way the Gmail API does."""
    return base64.urlsafe_b64encode(text.encode()).decode()


# ---------------------------------------------------------------------------
# _strip_html
# ---------------------------------------------------------------------------


def test_strip_html_removes_tags():
    """_strip_html() strips HTML markup and returns plain text."""
    result = _strip_html("<p>Hello <b>world</b></p>")
    assert "Hello world" in result
    assert "<" not in result


def test_strip_html_removes_style_block():
    """_strip_html() removes <style> blocks entirely."""
    html = "<style>body { color: red; }</style><p>Content</p>"
    result = _strip_html(html)
    assert "color" not in result
    assert "Content" in result


def test_strip_html_removes_script_block():
    """_strip_html() removes <script> blocks entirely."""
    html = "<script>alert('xss')</script><p>Safe</p>"
    result = _strip_html(html)
    assert "alert" not in result
    assert "Safe" in result


def test_strip_html_converts_br_to_newline():
    """_strip_html() converts <br> tags to newline characters."""
    result = _strip_html("line1<br>line2<br/>line3")
    assert "line1\nline2\nline3" == result


def test_strip_html_decodes_html_entities():
    """_strip_html() decodes &amp;, &lt;, &gt; and similar entities."""
    result = _strip_html("&lt;tag&gt; &amp; &quot;quote&quot;")
    assert "<tag>" in result
    assert "&" in result
    assert '"quote"' in result


def test_strip_html_collapses_multiple_blank_lines():
    """_strip_html() collapses 3+ consecutive newlines into two."""
    html = "<p>A</p><p></p><p></p><p>B</p>"
    result = _strip_html(html)
    # Should not have three consecutive newlines
    assert "\n\n\n" not in result


def test_strip_html_strips_surrounding_whitespace():
    """_strip_html() strips leading and trailing whitespace."""
    result = _strip_html("  <p>hello</p>  ")
    assert result == result.strip()


# ---------------------------------------------------------------------------
# _decode_body — leaf node (has body data)
# ---------------------------------------------------------------------------


def test_decode_body_leaf_plain_text():
    """_decode_body() decodes a simple leaf part with body data."""
    payload = {"body": {"data": _b64("Hello, world!")}}
    assert _decode_body(payload) == "Hello, world!"


def test_decode_body_returns_empty_for_missing_data():
    """_decode_body() returns empty string when there is no data and no parts."""
    payload = {"body": {}}
    assert _decode_body(payload) == ""


def test_decode_body_returns_empty_for_empty_payload():
    """_decode_body() returns empty string for a fully empty payload."""
    assert _decode_body({}) == ""


# ---------------------------------------------------------------------------
# _decode_body — multipart: plain wins over html
# ---------------------------------------------------------------------------


def test_decode_body_prefers_plain_over_html():
    """_decode_body() returns text/plain content when both plain and html are present."""
    payload = {
        "mimeType": "multipart/alternative",
        "body": {},
        "parts": [
            {
                "mimeType": "text/html",
                "body": {"data": _b64("<p>HTML version</p>")},
            },
            {
                "mimeType": "text/plain",
                "body": {"data": _b64("Plain version")},
            },
        ],
    }
    result = _decode_body(payload)
    assert result == "Plain version"


def test_decode_body_falls_back_to_stripped_html_when_no_plain():
    """_decode_body() strips HTML and returns readable text when only html part exists."""
    payload = {
        "mimeType": "multipart/alternative",
        "body": {},
        "parts": [
            {
                "mimeType": "text/html",
                "body": {"data": _b64("<p>Only HTML here</p>")},
            },
        ],
    }
    result = _decode_body(payload)
    assert "Only HTML here" in result
    assert "<p>" not in result


def test_decode_body_plain_part_listed_before_html():
    """_decode_body() returns plain text even when it appears before html in parts list."""
    payload = {
        "mimeType": "multipart/alternative",
        "body": {},
        "parts": [
            {
                "mimeType": "text/plain",
                "body": {"data": _b64("Plain first")},
            },
            {
                "mimeType": "text/html",
                "body": {"data": _b64("<p>HTML second</p>")},
            },
        ],
    }
    result = _decode_body(payload)
    assert result == "Plain first"


# ---------------------------------------------------------------------------
# _decode_body — nested multipart (e.g. multipart/mixed wrapping multipart/alternative)
# ---------------------------------------------------------------------------


def test_decode_body_nested_multipart_extracts_plain():
    """_decode_body() recurses into nested multipart parts to find text/plain."""
    payload = {
        "mimeType": "multipart/mixed",
        "body": {},
        "parts": [
            {
                "mimeType": "multipart/alternative",
                "body": {},
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": _b64("Nested plain")},
                    },
                    {
                        "mimeType": "text/html",
                        "body": {"data": _b64("<p>Nested HTML</p>")},
                    },
                ],
            }
        ],
    }
    result = _decode_body(payload)
    assert result == "Nested plain"


def test_decode_body_last_resort_returns_first_decodable_part():
    """_decode_body() returns the first decodable part when no plain or html found."""
    payload = {
        "mimeType": "multipart/mixed",
        "body": {},
        "parts": [
            {
                "mimeType": "application/octet-stream",
                "body": {"data": _b64("binary-ish content")},
            },
        ],
    }
    result = _decode_body(payload)
    assert result == "binary-ish content"
