"""Unit tests for draft_service module."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.email import EmailStatus
from tests.services.conftest import make_email, make_user

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _scalars_first(item):
    scalars_mock = MagicMock()
    scalars_mock.first.return_value = item
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    return result_mock


def _scalars_all(items):
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = items
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    return result_mock


# ---------------------------------------------------------------------------
# list_drafts()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_drafts_returns_drafted_and_needs_review(mock_db):
    """list_drafts() returns emails in DRAFTED or NEEDS_REVIEW state."""
    from app.services.draft_service import list_drafts

    user_id = uuid.uuid4()
    drafted = make_email(user_id=user_id, status=EmailStatus.DRAFTED, draft_response="hi")
    needs_review = make_email(user_id=user_id, status=EmailStatus.NEEDS_REVIEW, draft_response="ho")
    mock_db.execute = AsyncMock(return_value=_scalars_all([drafted, needs_review]))

    result = await list_drafts(mock_db, user_id)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_list_drafts_returns_empty_when_none(mock_db):
    """list_drafts() returns an empty list when there are no drafts."""
    from app.services.draft_service import list_drafts

    mock_db.execute = AsyncMock(return_value=_scalars_all([]))

    result = await list_drafts(mock_db, uuid.uuid4())

    assert result == []


# ---------------------------------------------------------------------------
# approve_draft()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_approve_draft_sends_email_and_marks_sent(mock_db):
    """approve_draft() sends via Gmail and updates status to SENT."""
    from app.services.draft_service import approve_draft

    user = make_user(oauth_token_encrypted="enc_token")
    email = make_email(
        user_id=user.id,
        status=EmailStatus.DRAFTED,
        draft_response="Hello back!",
    )
    mock_db.execute = AsyncMock(return_value=_scalars_first(email))

    mock_gmail = AsyncMock()
    mock_gmail.send_email = AsyncMock(return_value={"id": "sent-id"})

    with (
        patch("app.services.draft_service.decrypt_oauth_token", return_value="plain_token"),
        patch("app.services.draft_service.GmailClient", return_value=mock_gmail),
    ):
        result = await approve_draft(mock_db, user, email.id)

    assert result["status"] == "sent"
    assert email.status == EmailStatus.SENT
    mock_gmail.send_email.assert_awaited_once()
    mock_db.flush.assert_awaited()


@pytest.mark.asyncio
async def test_approve_draft_raises_404_when_not_found(mock_db):
    """approve_draft() raises HTTP 404 when the email does not exist."""
    from fastapi import HTTPException

    from app.services.draft_service import approve_draft

    user = make_user(oauth_token_encrypted="enc_token")
    mock_db.execute = AsyncMock(return_value=_scalars_first(None))

    with pytest.raises(HTTPException) as exc_info:
        await approve_draft(mock_db, user, uuid.uuid4())

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_approve_draft_raises_409_if_not_draft_state(mock_db):
    """approve_draft() raises HTTP 409 if the email is not in a draft-ready state."""
    from fastapi import HTTPException

    from app.services.draft_service import approve_draft

    user = make_user(oauth_token_encrypted="enc_token")
    email = make_email(user_id=user.id, status=EmailStatus.SENT)
    mock_db.execute = AsyncMock(return_value=_scalars_first(email))

    with pytest.raises(HTTPException) as exc_info:
        await approve_draft(mock_db, user, email.id)

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_approve_draft_raises_400_if_no_draft_content(mock_db):
    """approve_draft() raises HTTP 400 when there is no draft response to send."""
    from fastapi import HTTPException

    from app.services.draft_service import approve_draft

    user = make_user(oauth_token_encrypted="enc_token")
    email = make_email(user_id=user.id, status=EmailStatus.DRAFTED, draft_response=None)
    mock_db.execute = AsyncMock(return_value=_scalars_first(email))

    with pytest.raises(HTTPException) as exc_info:
        await approve_draft(mock_db, user, email.id)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_approve_draft_raises_400_if_no_gmail_connection(mock_db):
    """approve_draft() raises HTTP 400 when no Gmail OAuth token is stored."""
    from fastapi import HTTPException

    from app.services.draft_service import approve_draft

    user = make_user(oauth_token_encrypted=None)
    email = make_email(user_id=user.id, status=EmailStatus.DRAFTED, draft_response="hello")
    mock_db.execute = AsyncMock(return_value=_scalars_first(email))

    with pytest.raises(HTTPException) as exc_info:
        await approve_draft(mock_db, user, email.id)

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_approve_draft_raises_502_on_gmail_error(mock_db):
    """approve_draft() raises HTTP 502 when Gmail send fails."""
    import httpx as real_httpx
    from fastapi import HTTPException

    from app.services.draft_service import approve_draft

    user = make_user(oauth_token_encrypted="enc_token")
    email = make_email(user_id=user.id, status=EmailStatus.DRAFTED, draft_response="Hi!")
    mock_db.execute = AsyncMock(return_value=_scalars_first(email))

    fake_response = MagicMock()
    fake_response.status_code = 500
    fake_response.text = "Internal error"

    mock_gmail = AsyncMock()
    mock_gmail.send_email = AsyncMock(
        side_effect=real_httpx.HTTPStatusError(
            "500", request=MagicMock(), response=fake_response
        )
    )

    with (
        patch("app.services.draft_service.decrypt_oauth_token", return_value="plain_token"),
        patch("app.services.draft_service.GmailClient", return_value=mock_gmail),
    ):
        with pytest.raises(HTTPException) as exc_info:
            await approve_draft(mock_db, user, email.id)

    assert exc_info.value.status_code == 502


# ---------------------------------------------------------------------------
# reject_draft()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reject_draft_marks_email_rejected(mock_db):
    """reject_draft() updates the email status to REJECTED."""
    from app.services.draft_service import reject_draft

    user_id = uuid.uuid4()
    email = make_email(user_id=user_id, status=EmailStatus.DRAFTED)
    mock_db.execute = AsyncMock(return_value=_scalars_first(email))

    result = await reject_draft(mock_db, user_id, email.id)

    assert result["status"] == "rejected"
    assert email.status == EmailStatus.REJECTED
    mock_db.flush.assert_awaited()


@pytest.mark.asyncio
async def test_reject_draft_raises_404_when_not_found(mock_db):
    """reject_draft() raises HTTP 404 when the email does not exist."""
    from fastapi import HTTPException

    from app.services.draft_service import reject_draft

    mock_db.execute = AsyncMock(return_value=_scalars_first(None))

    with pytest.raises(HTTPException) as exc_info:
        await reject_draft(mock_db, uuid.uuid4(), uuid.uuid4())

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_reject_draft_raises_409_if_not_draft_state(mock_db):
    """reject_draft() raises HTTP 409 if the email is not in a draft-ready state."""
    from fastapi import HTTPException

    from app.services.draft_service import reject_draft

    user_id = uuid.uuid4()
    email = make_email(user_id=user_id, status=EmailStatus.PENDING)
    mock_db.execute = AsyncMock(return_value=_scalars_first(email))

    with pytest.raises(HTTPException) as exc_info:
        await reject_draft(mock_db, user_id, email.id)

    assert exc_info.value.status_code == 409


# ---------------------------------------------------------------------------
# edit_draft()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_edit_draft_updates_draft_response(mock_db):
    """edit_draft() replaces the draft_response text."""
    from app.services.draft_service import edit_draft

    user_id = uuid.uuid4()
    email = make_email(user_id=user_id, status=EmailStatus.DRAFTED, draft_response="old text")
    mock_db.execute = AsyncMock(return_value=_scalars_first(email))
    mock_db.refresh = AsyncMock()

    await edit_draft(mock_db, user_id, email.id, "new text")

    assert email.draft_response == "new text"
    mock_db.flush.assert_awaited()
    mock_db.refresh.assert_awaited_with(email)


@pytest.mark.asyncio
async def test_edit_draft_raises_404_when_not_found(mock_db):
    """edit_draft() raises HTTP 404 when the email does not exist."""
    from fastapi import HTTPException

    from app.services.draft_service import edit_draft

    mock_db.execute = AsyncMock(return_value=_scalars_first(None))

    with pytest.raises(HTTPException) as exc_info:
        await edit_draft(mock_db, uuid.uuid4(), uuid.uuid4(), "text")

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_edit_draft_raises_409_if_not_draft_state(mock_db):
    """edit_draft() raises HTTP 409 if the email is not editable."""
    from fastapi import HTTPException

    from app.services.draft_service import edit_draft

    user_id = uuid.uuid4()
    email = make_email(user_id=user_id, status=EmailStatus.REJECTED)
    mock_db.execute = AsyncMock(return_value=_scalars_first(email))

    with pytest.raises(HTTPException) as exc_info:
        await edit_draft(mock_db, user_id, email.id, "new text")

    assert exc_info.value.status_code == 409
