"""Gmail API client using httpx and Google OAuth2 credentials."""

from __future__ import annotations

import base64
import datetime
import logging
from email.mime.text import MIMEText
from typing import Any

import httpx

logger = logging.getLogger(__name__)

GMAIL_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"


class GmailClient:
    """Async Gmail API client backed by Google OAuth2 credentials."""

    def __init__(self, credentials: dict[str, Any]) -> None:
        self._credentials = credentials

    def _access_token(self) -> str:
        return self._credentials["access_token"]

    def _auth_headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token()}"}

    async def _refresh_if_needed(self, client: httpx.AsyncClient) -> None:
        from app.core.config import settings

        refresh_token = self._credentials.get("refresh_token")
        if not refresh_token:
            return

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
            self._credentials["access_token"] = token_data["access_token"]
            logger.debug("Gmail access token refreshed successfully")
        else:
            logger.warning(
                "Failed to refresh Gmail token: %s %s",
                response.status_code,
                response.text,
            )

    async def fetch_emails(self, max_results: int = 50) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            await self._refresh_if_needed(client)

            list_response = await client.get(
                f"{GMAIL_API_BASE}/messages",
                headers=self._auth_headers(),
                params={"maxResults": max_results, "labelIds": "INBOX"},
            )
            list_response.raise_for_status()
            messages = list_response.json().get("messages", [])

            emails: list[dict[str, Any]] = []
            for msg in messages:
                try:
                    email_data = await self._fetch_message(client, msg["id"])
                    emails.append(email_data)
                except httpx.HTTPStatusError as exc:
                    logger.warning("Failed to fetch email %s: %s", msg["id"], exc)

        return emails

    async def get_email(self, gmail_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient() as client:
            await self._refresh_if_needed(client)
            return await self._fetch_message(client, gmail_id)

    async def _fetch_message(
        self, client: httpx.AsyncClient, gmail_id: str
    ) -> dict[str, Any]:
        response = await client.get(
            f"{GMAIL_API_BASE}/messages/{gmail_id}",
            headers=self._auth_headers(),
            params={"format": "full"},
        )
        response.raise_for_status()
        return _parse_message(response.json())

    async def send_email(self, to: str, subject: str, body: str) -> dict[str, Any]:
        raw = _build_raw_message(to=to, subject=subject, body=body)
        async with httpx.AsyncClient() as client:
            await self._refresh_if_needed(client)
            response = await client.post(
                f"{GMAIL_API_BASE}/messages/send",
                headers={**self._auth_headers(), "Content-Type": "application/json"},
                json={"raw": raw},
            )
            response.raise_for_status()
            data = response.json()
            logger.info("Email sent, Gmail message id: %s", data.get("id"))
            return data

    async def create_draft(self, to: str, subject: str, body: str) -> dict[str, Any]:
        raw = _build_raw_message(to=to, subject=subject, body=body)
        async with httpx.AsyncClient() as client:
            await self._refresh_if_needed(client)
            response = await client.post(
                f"{GMAIL_API_BASE}/drafts",
                headers={**self._auth_headers(), "Content-Type": "application/json"},
                json={"message": {"raw": raw}},
            )
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


def _decode_body(payload: dict[str, Any]) -> str:
    body_data = payload.get("body", {}).get("data", "")

    if body_data:
        try:
            return base64.urlsafe_b64decode(body_data + "==").decode("utf-8", errors="replace")
        except Exception:
            logger.debug("Failed to decode message body part")

    for part in payload.get("parts", []):
        text = _decode_body(part)
        if text:
            return text

    return ""


def _parse_message(raw: dict[str, Any]) -> dict[str, Any]:
    payload = raw.get("payload", {})
    headers = payload.get("headers", [])

    internal_date_ms = int(raw.get("internalDate", 0))
    received_at = datetime.datetime.fromtimestamp(
        internal_date_ms / 1000, tz=datetime.timezone.utc
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
    }


def _build_raw_message(to: str, subject: str, body: str) -> str:
    msg = MIMEText(body, "plain", "utf-8")
    msg["To"] = to
    msg["Subject"] = subject
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")
