"""Gmail OAuth2 flow helpers."""

from __future__ import annotations

import logging
import urllib.parse

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/calendar.events",
]


def get_oauth_url(redirect_uri: str | None = None) -> str:
    effective_redirect = redirect_uri or settings.GMAIL_REDIRECT_URI
    scope = " ".join(GMAIL_SCOPES)

    params = urllib.parse.urlencode(
        {
            "client_id": settings.GMAIL_CLIENT_ID,
            "redirect_uri": effective_redirect,
            "response_type": "code",
            "scope": scope,
            "access_type": "offline",
            "prompt": "consent",
        }
    )
    url = f"{GOOGLE_AUTH_URL}?{params}"
    logger.debug("Generated OAuth URL for redirect_uri=%s", effective_redirect)
    return url


async def exchange_code(code: str, redirect_uri: str | None = None) -> dict[str, str]:
    effective_redirect = redirect_uri or settings.GMAIL_REDIRECT_URI

    async with httpx.AsyncClient() as client:
        response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.GMAIL_CLIENT_ID,
                "client_secret": settings.GMAIL_CLIENT_SECRET,
                "redirect_uri": effective_redirect,
                "grant_type": "authorization_code",
            },
        )
        response.raise_for_status()
        token_data: dict[str, str] = response.json()

    logger.info("OAuth code exchange successful, scopes: %s", token_data.get("scope"))
    return token_data
