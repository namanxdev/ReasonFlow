# Gmail Integration

## Overview

ReasonFlow connects to Gmail via OAuth2 to fetch, classify, and respond to emails automatically.

## OAuth2 Flow

```
User clicks "Connect Gmail"
→ GET /auth/gmail/url → redirect to Google consent screen
→ User grants permissions
→ Google redirects to /auth/gmail/callback with code
→ Backend exchanges code for access + refresh tokens
→ Tokens encrypted and stored in users table
```

### Required Scopes
- `https://www.googleapis.com/auth/gmail.readonly` — Read emails
- `https://www.googleapis.com/auth/gmail.send` — Send emails
- `https://www.googleapis.com/auth/gmail.compose` — Create drafts

## GmailClient API

```python
class GmailClient:
    async def fetch_emails(max_results=50) -> list[dict]
    async def get_email(gmail_id: str) -> dict
    async def send_email(to: str, subject: str, body: str) -> str
    async def create_draft(to: str, subject: str, body: str) -> str
```

All calls use `httpx.AsyncClient` with the Google Gmail REST API v1.

## Token Management

- Access tokens: short-lived (~1 hour), auto-refreshed on expiry
- Refresh tokens: stored encrypted (Fernet symmetric encryption)
- Token refresh: automatic via `refresh_token()` before API calls

## Email Sync

`GET /emails/sync` triggers:
1. Fetch latest emails from Gmail API
2. Deduplicate by `gmail_id`
3. Store new emails in database with `status=pending`
4. Return count of new emails

## Security

- OAuth tokens encrypted at rest using `cryptography.fernet`
- Client secret stored only in environment variables
- Redirect URI validated against configured value
- Token auto-revocation on user disconnect
