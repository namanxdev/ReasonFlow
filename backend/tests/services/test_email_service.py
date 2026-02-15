"""Unit tests for email_service module."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.email import EmailClassification, EmailStatus
from app.schemas.email import EmailFilterParams
from tests.services.conftest import make_email, make_user


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _scalars_all(items: list):
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = items
    result_mock = AsyncMock()
    result_mock.scalars.return_value = scalars_mock
    return result_mock


def _scalars_first(item):
    scalars_mock = MagicMock()
    scalars_mock.first.return_value = item
    result_mock = AsyncMock()
    result_mock.scalars.return_value = scalars_mock
    return result_mock


# ---------------------------------------------------------------------------
# list_emails()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_emails_returns_items_and_total(mock_db):
    """list_emails() returns all matching emails and the correct total count."""
    from app.services.email_service import list_emails

    user_id = uuid.uuid4()
    emails = [make_email(user_id=user_id), make_email(user_id=user_id)]

    # First execute call = count query, second = paginated query.
    mock_db.execute = AsyncMock(
        side_effect=[
            _scalars_all(emails),  # count
            _scalars_all(emails),  # paginated page
        ]
    )

    filters = EmailFilterParams()
    items, total = await list_emails(mock_db, user_id, filters)

    assert total == 2
    assert len(items) == 2


@pytest.mark.asyncio
async def test_list_emails_applies_status_filter(mock_db):
    """list_emails() includes the status filter in the query."""
    from app.services.email_service import list_emails

    user_id = uuid.uuid4()
    email = make_email(user_id=user_id, status=EmailStatus.DRAFTED)
    mock_db.execute = AsyncMock(
        side_effect=[
            _scalars_all([email]),
            _scalars_all([email]),
        ]
    )

    filters = EmailFilterParams(status=EmailStatus.DRAFTED)
    items, total = await list_emails(mock_db, user_id, filters)

    assert total == 1
    assert items[0].status == EmailStatus.DRAFTED


@pytest.mark.asyncio
async def test_list_emails_empty_result(mock_db):
    """list_emails() returns empty list and zero total when no emails match."""
    from app.services.email_service import list_emails

    mock_db.execute = AsyncMock(
        side_effect=[
            _scalars_all([]),
            _scalars_all([]),
        ]
    )

    filters = EmailFilterParams()
    items, total = await list_emails(mock_db, uuid.uuid4(), filters)

    assert total == 0
    assert items == []


# ---------------------------------------------------------------------------
# get_email()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_email_returns_email_for_owner(mock_db):
    """get_email() returns the email when the caller owns it."""
    from app.services.email_service import get_email

    user_id = uuid.uuid4()
    email = make_email(user_id=user_id)
    mock_db.execute = AsyncMock(return_value=_scalars_first(email))

    result = await get_email(mock_db, user_id, email.id)

    assert result.id == email.id


@pytest.mark.asyncio
async def test_get_email_raises_404_when_not_found(mock_db):
    """get_email() raises HTTP 404 when the email does not exist."""
    from fastapi import HTTPException

    from app.services.email_service import get_email

    mock_db.execute = AsyncMock(return_value=_scalars_first(None))

    with pytest.raises(HTTPException) as exc_info:
        await get_email(mock_db, uuid.uuid4(), uuid.uuid4())

    assert exc_info.value.status_code == 404


# ---------------------------------------------------------------------------
# sync_emails()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_emails_raises_400_if_no_oauth_token(mock_db):
    """sync_emails() raises HTTP 400 when Gmail is not connected."""
    from fastapi import HTTPException

    from app.services.email_service import sync_emails

    user = make_user(oauth_token_encrypted=None)

    with pytest.raises(HTTPException) as exc_info:
        await sync_emails(mock_db, user)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_sync_emails_creates_new_email_records(mock_db):
    """sync_emails() persists emails from Gmail that are not yet in the DB."""
    from app.services.email_service import sync_emails

    user = make_user(oauth_token_encrypted="enc_token")
    raw_emails = [
        {
            "gmail_id": "gid-1",
            "thread_id": "t1",
            "subject": "Test",
            "sender": "a@example.com",
            "recipient": "b@example.com",
            "body": "Hello",
            "received_at": "2026-01-01T10:00:00+00:00",
        }
    ]

    # First execute = existing check (returns None = not a duplicate).
    mock_db.execute = AsyncMock(return_value=_scalars_first(None))

    with (
        patch("app.services.email_service.decrypt_oauth_token", return_value="plain_token"),
        patch(
            "app.services.email_service.GmailClient.fetch_emails",
            AsyncMock(return_value=raw_emails),
        ),
    ):
        result = await sync_emails(mock_db, user)

    assert result["fetched"] == 1
    assert result["created"] == 1
    mock_db.add.assert_called_once()


@pytest.mark.asyncio
async def test_sync_emails_skips_duplicates(mock_db):
    """sync_emails() does not insert an email whose gmail_id already exists."""
    from app.services.email_service import sync_emails

    user = make_user(oauth_token_encrypted="enc_token")
    existing_email = make_email(gmail_id="gid-1")
    raw_emails = [
        {
            "gmail_id": "gid-1",
            "subject": "Dup",
            "sender": "a@example.com",
            "body": "Body",
            "received_at": "2026-01-01T10:00:00+00:00",
        }
    ]

    mock_db.execute = AsyncMock(return_value=_scalars_first(existing_email))

    with (
        patch("app.services.email_service.decrypt_oauth_token", return_value="plain_token"),
        patch(
            "app.services.email_service.GmailClient.fetch_emails",
            AsyncMock(return_value=raw_emails),
        ),
    ):
        result = await sync_emails(mock_db, user)

    assert result["fetched"] == 1
    assert result["created"] == 0
    mock_db.add.assert_not_called()


@pytest.mark.asyncio
async def test_sync_emails_raises_502_on_gmail_error(mock_db):
    """sync_emails() raises HTTP 502 when the Gmail API returns an error."""
    import httpx as real_httpx

    from fastapi import HTTPException

    from app.services.email_service import sync_emails

    user = make_user(oauth_token_encrypted="enc_token")

    fake_response = MagicMock()
    fake_response.status_code = 401
    fake_response.text = "Unauthorized"

    with (
        patch("app.services.email_service.decrypt_oauth_token", return_value="plain_token"),
        patch(
            "app.services.email_service.GmailClient.fetch_emails",
            AsyncMock(
                side_effect=real_httpx.HTTPStatusError(
                    "401", request=MagicMock(), response=fake_response
                )
            ),
        ),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await sync_emails(mock_db, user)

    assert exc_info.value.status_code == 502


# ---------------------------------------------------------------------------
# process_email()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_process_email_returns_trace_id(mock_db):
    """process_email() creates an AgentLog entry and returns a trace_id."""
    from app.services.email_service import process_email

    user = make_user()
    email = make_email(user_id=user.id, status=EmailStatus.PENDING)
    mock_db.execute = AsyncMock(return_value=_scalars_first(email))

    result = await process_email(mock_db, user, email.id)

    assert "trace_id" in result
    assert result["status"] == "processing"
    assert email.status == EmailStatus.PROCESSING
    mock_db.add.assert_called_once()  # AgentLog added


@pytest.mark.asyncio
async def test_process_email_raises_404_when_not_found(mock_db):
    """process_email() raises HTTP 404 when the email does not exist."""
    from fastapi import HTTPException

    from app.services.email_service import process_email

    user = make_user()
    mock_db.execute = AsyncMock(return_value=_scalars_first(None))

    with pytest.raises(HTTPException) as exc_info:
        await process_email(mock_db, user, uuid.uuid4())

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_process_email_raises_409_if_already_processing(mock_db):
    """process_email() raises HTTP 409 for an email already in processing state."""
    from fastapi import HTTPException

    from app.services.email_service import process_email

    user = make_user()
    email = make_email(user_id=user.id, status=EmailStatus.PROCESSING)
    mock_db.execute = AsyncMock(return_value=_scalars_first(email))

    with pytest.raises(HTTPException) as exc_info:
        await process_email(mock_db, user, email.id)

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_process_email_raises_409_if_already_sent(mock_db):
    """process_email() raises HTTP 409 for an email that has already been sent."""
    from fastapi import HTTPException

    from app.services.email_service import process_email

    user = make_user()
    email = make_email(user_id=user.id, status=EmailStatus.SENT)
    mock_db.execute = AsyncMock(return_value=_scalars_first(email))

    with pytest.raises(HTTPException) as exc_info:
        await process_email(mock_db, user, email.id)

    assert exc_info.value.status_code == 409
