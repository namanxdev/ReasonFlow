"""Unit tests for CRM auto-populate logic in sync_emails."""

from __future__ import annotations

import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _make_user(oauth_token_encrypted: str | None = "enc_token") -> SimpleNamespace:
    """Return a lightweight user-like object usable without SQLAlchemy."""
    return SimpleNamespace(
        id=uuid.uuid4(),
        oauth_token_encrypted=oauth_token_encrypted,
        oauth_refresh_token_encrypted=None,
    )


def _scalars_first(item):
    """Mock helper: return an execute result whose .scalars().first() == item.

    Uses MagicMock (not AsyncMock) so that .scalars() returns a plain mock,
    not a coroutine.
    """
    scalars_mock = MagicMock()
    scalars_mock.first.return_value = item
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    return result_mock


def _make_db() -> MagicMock:
    """Return a minimal async-compatible DB session mock."""
    db = MagicMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.execute = AsyncMock(return_value=_scalars_first(None))
    return db


# ---------------------------------------------------------------------------
# sync_emails() — CRM auto-populate
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_emails_auto_creates_crm_contact_for_new_sender():
    """sync_emails() creates a CRM contact for a sender not already in the CRM."""
    from app.integrations.crm.mock_crm import MockCRM
    from app.services.email_service import sync_emails

    user = _make_user()
    mock_db = _make_db()
    raw_emails = [
        {
            "gmail_id": "gid-new",
            "thread_id": "t1",
            "subject": "Hello",
            "sender": "New Person <new@sender.com>",
            "recipient": "me@example.com",
            "body": "Hi",
            "received_at": "2026-01-01T10:00:00+00:00",
        }
    ]

    crm = MockCRM()
    with (
        patch("app.services.email_service.decrypt_oauth_token", return_value="plain_token"),
        patch(
            "app.services.email_service.GmailClient.fetch_emails",
            AsyncMock(return_value=raw_emails),
        ),
        patch(
            "app.services.email_service.get_gemini_client",
            side_effect=RuntimeError("no gemini in test"),
        ),
        patch(
            "app.integrations.crm.factory.get_crm_client",
            return_value=crm,
        ),
    ):
        result = await sync_emails(mock_db, user)

    assert result["fetched"] == 1
    contact = await crm.get_contact("new@sender.com")
    assert contact is not None
    assert contact["name"] == "New Person"
    assert "auto-synced" in contact["tags"]


@pytest.mark.asyncio
async def test_sync_emails_skips_crm_update_for_existing_contact():
    """sync_emails() does not overwrite a contact that already exists in the CRM."""
    from app.integrations.crm.mock_crm import MockCRM
    from app.services.email_service import sync_emails

    user = _make_user()
    mock_db = _make_db()
    # alice@example.com is pre-seeded in MockCRM
    raw_emails = [
        {
            "gmail_id": "gid-alice",
            "thread_id": "t1",
            "subject": "Hi",
            "sender": "Alice Smith <alice@example.com>",
            "recipient": "me@example.com",
            "body": "Body",
            "received_at": "2026-01-01T10:00:00+00:00",
        }
    ]

    crm = MockCRM()
    with (
        patch("app.services.email_service.decrypt_oauth_token", return_value="plain_token"),
        patch(
            "app.services.email_service.GmailClient.fetch_emails",
            AsyncMock(return_value=raw_emails),
        ),
        patch(
            "app.services.email_service.get_gemini_client",
            side_effect=RuntimeError("no gemini in test"),
        ),
        patch(
            "app.integrations.crm.factory.get_crm_client",
            return_value=crm,
        ),
    ):
        await sync_emails(mock_db, user)

    # alice should NOT have been overwritten with auto-synced data
    contact = await crm.get_contact("alice@example.com")
    assert contact is not None
    assert contact["name"] == "Alice Smith"
    assert "auto-synced" not in contact.get("tags", [])


@pytest.mark.asyncio
async def test_sync_emails_deduplicates_senders_across_raw_emails():
    """sync_emails() creates only one CRM contact per unique sender email."""
    from app.integrations.crm.mock_crm import MockCRM
    from app.services.email_service import sync_emails

    user = _make_user()
    mock_db = _make_db()
    # Same sender appears twice in the raw email list
    raw_emails = [
        {
            "gmail_id": "gid-1",
            "sender": "dup@example.com",
            "subject": "First",
            "body": "A",
            "received_at": "2026-01-01T10:00:00+00:00",
        },
        {
            "gmail_id": "gid-2",
            "sender": "dup@example.com",
            "subject": "Second",
            "body": "B",
            "received_at": "2026-01-02T10:00:00+00:00",
        },
    ]

    crm = MockCRM()
    with (
        patch("app.services.email_service.decrypt_oauth_token", return_value="plain_token"),
        patch(
            "app.services.email_service.GmailClient.fetch_emails",
            AsyncMock(return_value=raw_emails),
        ),
        patch(
            "app.services.email_service.get_gemini_client",
            side_effect=RuntimeError("no gemini in test"),
        ),
        patch(
            "app.integrations.crm.factory.get_crm_client",
            return_value=crm,
        ),
    ):
        await sync_emails(mock_db, user)

    # Only one contact entry for the deduplicated sender
    results = await crm.search_contacts("dup@example.com")
    assert len(results) == 1


@pytest.mark.asyncio
async def test_sync_emails_crm_failure_does_not_raise():
    """sync_emails() swallows CRM errors and still returns the sync counts."""
    from app.services.email_service import sync_emails

    user = _make_user()
    mock_db = _make_db()
    raw_emails = [
        {
            "gmail_id": "gid-crm-err",
            "sender": "fail@example.com",
            "subject": "Boom",
            "body": "x",
            "received_at": "2026-01-01T10:00:00+00:00",
        }
    ]

    with (
        patch("app.services.email_service.decrypt_oauth_token", return_value="plain_token"),
        patch(
            "app.services.email_service.GmailClient.fetch_emails",
            AsyncMock(return_value=raw_emails),
        ),
        patch(
            "app.services.email_service.get_gemini_client",
            side_effect=RuntimeError("no gemini in test"),
        ),
        patch(
            "app.integrations.crm.factory.get_crm_client",
            side_effect=RuntimeError("CRM unavailable"),
        ),
    ):
        result = await sync_emails(mock_db, user)

    # CRM failure must not propagate — email sync counts should be returned
    assert result["fetched"] == 1


@pytest.mark.asyncio
async def test_sync_emails_extracts_plain_email_without_angle_brackets():
    """sync_emails() handles a sender that is just an email address with no display name."""
    from app.integrations.crm.mock_crm import MockCRM
    from app.services.email_service import sync_emails

    user = _make_user()
    mock_db = _make_db()
    raw_emails = [
        {
            "gmail_id": "gid-plain",
            "sender": "plain@noname.com",
            "subject": "Plain",
            "body": "x",
            "received_at": "2026-01-01T10:00:00+00:00",
        }
    ]

    crm = MockCRM()
    with (
        patch("app.services.email_service.decrypt_oauth_token", return_value="plain_token"),
        patch(
            "app.services.email_service.GmailClient.fetch_emails",
            AsyncMock(return_value=raw_emails),
        ),
        patch(
            "app.services.email_service.get_gemini_client",
            side_effect=RuntimeError("no gemini in test"),
        ),
        patch(
            "app.integrations.crm.factory.get_crm_client",
            return_value=crm,
        ),
    ):
        await sync_emails(mock_db, user)

    contact = await crm.get_contact("plain@noname.com")
    assert contact is not None
    # No display name extracted for plain address senders
    assert contact["name"] == ""
