"""Gmail API client using httpx and Google OAuth2 credentials."""

from __future__ import annotations

import asyncio
import base64
import datetime
import logging
import time
from email.mime.text import MIMEText
from typing import Any, Callable

import httpx
from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.utils.sanitize import sanitize_html, strip_html_tags

logger = logging.getLogger(__name__)

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


class GmailRateLimitError(Exception):
    """Raised when Gmail API returns 429 rate limit exceeded."""

    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


def _get_retry_after(retry_state: RetryCallState) -> float:
    """Custom wait function that respects Retry-After header if present."""
    # Default exponential backoff: 2, 4, 8 seconds
    exp_wait = wait_exponential(multiplier=1, min=2, max=10)(retry_state)

    # Check if the last exception was a GmailRateLimitError with retry_after
    if retry_state.outcome is not None and retry_state.outcome.failed:
        exception = retry_state.outcome.exception()
        if isinstance(exception, GmailRateLimitError) and exception.retry_after is not None:
            # Use the Retry-After header value (capped at 60 seconds for safety)
            return min(exception.retry_after, 60)

    return exp_wait


class GmailClient:
    """Async Gmail API client backed by Google OAuth2 credentials.

    Supports automatic token refresh with optional callback to persist
    refreshed tokens to the database.
    """

    def __init__(
        self,
        credentials: dict[str, Any],
        on_token_refresh: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        """Initialize the Gmail client.

        Args:
            credentials: OAuth2 credentials dict with 'access_token' and optionally
                'refresh_token' and 'expires_at'.
            on_token_refresh: Optional callback invoked when token is refreshed.
                Called with the updated credentials dict containing new access_token
                and expires_at values.
        """
        self._credentials = credentials
        self._on_token_refresh = on_token_refresh

    def _access_token(self) -> str:
        return self._credentials["access_token"]

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token()}"}

    async def _refresh_if_needed(self, client: httpx.AsyncClient) -> None:
        from app.core.config import settings

        refresh_token = self._credentials.get("refresh_token")
        if not refresh_token:
            return

        # Check if token is expired or about to expire (within 60s buffer)
        expires_at = self._credentials.get("expires_at")
        if expires_at and time.time() < expires_at - 60:
            return  # Token still valid, no need to refresh

        response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.GMAIL_CLIENT_ID,
                "client_secret": settings.GMAIL_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
        )
        if response.status_code == 200:
            token_data = response.json()
            new_access_token = token_data["access_token"]
            expires_in = token_data.get("expires_in", 3600)
            new_expires_at = time.time() + expires_in

            # Update credentials in memory
            self._credentials["access_token"] = new_access_token
            self._credentials["expires_at"] = new_expires_at

            # Notify callback if provided (for database persistence)
            if self._on_token_refresh:
                try:
                    self._on_token_refresh(self._credentials.copy())
                except Exception as exc:
                    logger.warning("Token refresh callback failed: %s", exc)

            logger.debug("Gmail access token refreshed successfully")
        else:
            logger.warning(
                "Failed to refresh Gmail token: %s %s",
                response.status_code,
                response.text,
            )

    def _check_rate_limit(self, response: httpx.Response) -> None:
        """Check if response is a 429 rate limit error and raise GmailRateLimitError.
        
        Respects the Retry-After header if present in the response.
        """
        if response.status_code == 429:
            retry_after_header = response.headers.get("retry-after")
            retry_after = None
            if retry_after_header:
                try:
                    retry_after = int(retry_after_header)
                    logger.warning(
                        "Gmail API rate limit exceeded (429). Retry-After: %s seconds",
                        retry_after,
                    )
                except ValueError:
                    logger.warning(
                        "Gmail API rate limit exceeded (429). Invalid Retry-After header: %s",
                        retry_after_header,
                    )
            else:
                logger.warning("Gmail API rate limit exceeded (429). No Retry-After header.")
            raise GmailRateLimitError("Gmail API rate limit exceeded", retry_after=retry_after)

    @retry(
        retry=retry_if_exception_type((GmailRateLimitError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=_get_retry_after,
        reraise=True,
    )
    async def fetch_emails(self, max_results: int = 50) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            await self._refresh_if_needed(client)

            list_response = await client.get(
                f"{GMAIL_API_BASE}/messages",
                headers=self._auth_headers(),
                params={"maxResults": max_results, "labelIds": "INBOX"},
            )
            self._check_rate_limit(list_response)
            list_response.raise_for_status()
            messages = list_response.json().get("messages", [])

            # Fetch all message details concurrently with semaphore limit
            sem = asyncio.Semaphore(10)
            fetch_tasks = [
                self._fetch_message_with_semaphore(sem, client, msg["id"])
                for msg in messages
            ]
            results = await asyncio.gather(*fetch_tasks, return_exceptions=True)

            # Filter out exceptions and log failures
            emails: list[dict[str, Any]] = []
            for msg, result in zip(messages, results):
                if isinstance(result, Exception):
                    logger.warning("Failed to fetch email %s: %s", msg["id"], result)
                else:
                    emails.append(result)

        return emails

    @retry(
        retry=retry_if_exception_type((GmailRateLimitError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=_get_retry_after,
        reraise=True,
    )
    async def get_email(self, gmail_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            await self._refresh_if_needed(client)
            return await self._fetch_message(client, gmail_id)

    @retry(
        retry=retry_if_exception_type((GmailRateLimitError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=_get_retry_after,
        reraise=True,
    )
    async def _fetch_message(
        self, client: httpx.AsyncClient, gmail_id: str
    ) -> dict[str, Any]:
        response = await client.get(
            f"{GMAIL_API_BASE}/messages/{gmail_id}",
            headers=self._auth_headers(),
            params={"format": "full"},
        )
        self._check_rate_limit(response)
        response.raise_for_status()
        return _parse_message(response.json())

    async def _fetch_message_with_semaphore(
        self, sem: asyncio.Semaphore, client: httpx.AsyncClient, gmail_id: str
    ) -> dict[str, Any]:
        """Fetch a single message with semaphore-controlled concurrency.

        Args:
            sem: Semaphore to limit concurrent requests.
            client: The httpx async client.
            gmail_id: The Gmail message ID.

        Returns:
            Parsed message dict.
        """
        async with sem:
            return await self._fetch_message(client, gmail_id)

    @retry(
        retry=retry_if_exception_type((GmailRateLimitError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=_get_retry_after,
        reraise=True,
    )
    async def send_email(self, to: str, subject: str, body: str) -> dict[str, Any]:
        raw = _build_raw_message(to=to, subject=subject, body=body)
        async with httpx.AsyncClient() as client:
            await self._refresh_if_needed(client)
            response = await client.post(
                f"{GMAIL_API_BASE}/messages/send",
                headers={**self._auth_headers(), "Content-Type": "application/json"},
                json={"raw": raw},
            )
            self._check_rate_limit(response)
            response.raise_for_status()
            data = response.json()
            logger.info("Email sent, Gmail message id: %s", data.get("id"))
            return data

    @retry(
        retry=retry_if_exception_type((GmailRateLimitError, httpx.HTTPStatusError)),
        stop=stop_after_attempt(3),
        wait=_get_retry_after,
        reraise=True,
    )
    async def create_draft(self, to: str, subject: str, body: str) -> dict[str, Any]:
        raw = _build_raw_message(to=to, subject=subject, body=body)
        async with httpx.AsyncClient() as client:
            await self._refresh_if_needed(client)
            response = await client.post(
                f"{GMAIL_API_BASE}/drafts",
                headers={**self._auth_headers(), "Content-Type": "application/json"},
                json={"message": {"raw": raw}},
            )
            self._check_rate_limit(response)
            response.raise_for_status()
            data = response.json()
            logger.info("Draft created, draft id: %s", data.get("id"))
            return data


def build_service(credentials: dict[str, Any]) -> GmailClient:
    return GmailClient(credentials)


def _extract_header(headers: list[dict[str, str]], name: str) -> str:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def _strip_html(html: str) -> str:
    """Convert HTML to plain text.

    - Converts ``<br>`` / ``<br/>`` to newlines.
    - Removes ``<style>`` and ``<script>`` blocks entirely.
    - Strips remaining HTML tags.
    - Decodes HTML entities (``&amp;`` → ``&``).
    - Collapses 3+ consecutive newlines into two.
    - Strips surrounding whitespace.
    """
    import html as html_module
    import re

    text = html
    # Remove <style> blocks
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Remove <script> blocks
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Convert <br> variants to newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode HTML entities
    text = html_module.unescape(text)
    # Collapse 3+ consecutive newlines into two
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _decode_body(payload: dict[str, Any]) -> str:
    """Decode an email payload, preferring text/plain over text/html.

    For multipart messages, searches all parts for text/plain first.
    Falls back to text/html (with tags stripped) if no plain part exists.
    For leaf payloads with body data, decodes and strips HTML.
    """
    mime_type = payload.get("mimeType", "")
    parts = payload.get("parts", [])

    # Multipart: try to find text/plain, then text/html, then recurse.
    if parts:
        plain_text = ""
        html_text = ""
        for part in parts:
            part_mime = part.get("mimeType", "")
            if part_mime == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    try:
                        plain_text = base64.urlsafe_b64decode(data + "==").decode(
                            "utf-8", errors="replace"
                        )
                    except Exception:
                        logger.debug("Failed to decode text/plain part")
            elif part_mime == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    try:
                        html_text = base64.urlsafe_b64decode(data + "==").decode(
                            "utf-8", errors="replace"
                        )
                    except Exception:
                        logger.debug("Failed to decode text/html part")
            elif part.get("parts"):
                # Recurse into nested multipart
                nested = _decode_body(part)
                if nested:
                    return nested

        if plain_text:
            return plain_text
        if html_text:
            return _strip_html(html_text)

        # Last resort: return first decodable part
        for part in parts:
            data = part.get("body", {}).get("data", "")
            if data:
                try:
                    return base64.urlsafe_b64decode(data + "==").decode(
                        "utf-8", errors="replace"
                    )
                except Exception:
                    continue
        return ""

    # Leaf node: decode body data directly
    body_data = payload.get("body", {}).get("data", "")
    if body_data:
        try:
            decoded = base64.urlsafe_b64decode(body_data + "==").decode(
                "utf-8", errors="replace"
            )
            return _strip_html(decoded) if "<" in decoded else decoded
        except Exception:
            logger.debug("Failed to decode message body part")

    return ""


def _extract_attachments(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract attachment metadata from message payload.

    Recursively searches through payload parts to find attachments.
    An attachment is identified by having both a filename and an attachmentId.

    Args:
        payload: The message payload dict from Gmail API.

    Returns:
        List of attachment metadata dicts containing:
        - filename: The attachment filename
        - mime_type: The MIME type of the attachment
        - size: The attachment size in bytes
        - attachment_id: The Gmail attachment ID for fetching content
    """
    attachments: list[dict[str, Any]] = []
    parts = payload.get("parts", [])

    for part in parts:
        filename = part.get("filename", "")
        body = part.get("body", {})
        attachment_id = body.get("attachmentId")

        if filename and attachment_id:
            attachments.append({
                "filename": filename,
                "mime_type": part.get("mimeType", "application/octet-stream"),
                "size": body.get("size", 0),
                "attachment_id": attachment_id,
            })

        # Recursively check nested parts (e.g., multipart/mixed)
        if part.get("parts"):
            attachments.extend(_extract_attachments(part))

    return attachments


def _parse_message(raw: dict[str, Any]) -> dict[str, Any]:
    payload = raw.get("payload", {})
    headers = payload.get("headers", [])

    internal_date_ms = int(raw.get("internalDate", 0))
    received_at = datetime.datetime.fromtimestamp(
        internal_date_ms / 1000, tz=datetime.UTC
    ).isoformat()

    return {
        "gmail_id": raw.get("id", ""),
        "thread_id": raw.get("threadId", ""),
        "subject": _extract_header(headers, "Subject"),
        "sender": _extract_header(headers, "From"),
        "recipient": _extract_header(headers, "To"),
        "received_at": received_at,
        "body": _decode_body(payload),
        "snippet": raw.get("snippet", ""),
        "label_ids": raw.get("labelIds", []),
        "attachments": _extract_attachments(payload),
    }


def _build_raw_message(to: str, subject: str, body: str) -> str:
    msg = MIMEText(body, "plain", "utf-8")
    msg["To"] = to
    msg["Subject"] = subject
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
