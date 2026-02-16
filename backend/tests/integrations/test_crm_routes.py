"""Unit tests for CRM API route handlers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.integrations.crm.mock_crm import MockCRM

# ---------------------------------------------------------------------------
# MockCRM.search_contacts behaviour
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mock_crm_search_contacts_returns_all_on_empty_query():
    """search_contacts('') returns all contacts when query is empty string."""
    crm = MockCRM()
    results = await crm.search_contacts("")
    assert len(results) == 3
    emails = {c["email"] for c in results}
    assert "alice@example.com" in emails
    assert "bob@techcorp.io" in emails
    assert "carol@startup.dev" in emails


@pytest.mark.asyncio
async def test_mock_crm_search_contacts_filters_by_name():
    """search_contacts() returns only contacts whose name matches the query."""
    crm = MockCRM()
    results = await crm.search_contacts("alice")
    assert len(results) == 1
    assert results[0]["email"] == "alice@example.com"


@pytest.mark.asyncio
async def test_mock_crm_search_contacts_filters_by_email():
    """search_contacts() matches against the contact email field."""
    crm = MockCRM()
    results = await crm.search_contacts("techcorp")
    assert len(results) == 1
    assert results[0]["email"] == "bob@techcorp.io"


@pytest.mark.asyncio
async def test_mock_crm_search_contacts_returns_empty_for_no_match():
    """search_contacts() returns an empty list when nothing matches."""
    crm = MockCRM()
    results = await crm.search_contacts("nonexistent_xyz_123")
    assert results == []


@pytest.mark.asyncio
async def test_mock_crm_get_contact_returns_none_for_missing():
    """get_contact() returns None for an email that does not exist."""
    crm = MockCRM()
    result = await crm.get_contact("nobody@missing.io")
    assert result is None


@pytest.mark.asyncio
async def test_mock_crm_update_contact_creates_new_entry():
    """update_contact() creates a new contact record when the email is unknown."""
    crm = MockCRM()
    data = {"name": "New Person", "company": "New Co", "tags": ["auto-synced"]}
    result = await crm.update_contact("new@example.com", data)
    assert result["email"] == "new@example.com"
    assert result["name"] == "New Person"

    fetched = await crm.get_contact("new@example.com")
    assert fetched is not None
    assert fetched["tags"] == ["auto-synced"]


@pytest.mark.asyncio
async def test_mock_crm_update_contact_merges_existing():
    """update_contact() merges new fields into an existing contact."""
    crm = MockCRM()
    await crm.update_contact("alice@example.com", {"phone": "555-1234"})
    updated = await crm.get_contact("alice@example.com")
    assert updated is not None
    assert updated["phone"] == "555-1234"
    # Existing fields should be preserved
    assert updated["name"] == "Alice Smith"


# ---------------------------------------------------------------------------
# list_contacts route handler
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_contacts_returns_all_when_no_query():
    """list_contacts() returns all contacts when q is None."""
    from app.api.routes.crm import list_contacts

    mock_user = MagicMock()
    with patch(
        "app.api.routes.crm.get_crm_client",
        return_value=MockCRM(),
    ):
        results = await list_contacts(q=None, _user=mock_user)

    assert len(results) == 3
    emails = {r.email for r in results}
    assert "alice@example.com" in emails


@pytest.mark.asyncio
async def test_list_contacts_filters_by_query():
    """list_contacts() passes the query to search_contacts and filters results."""
    from app.api.routes.crm import list_contacts

    mock_user = MagicMock()
    with patch(
        "app.api.routes.crm.get_crm_client",
        return_value=MockCRM(),
    ):
        results = await list_contacts(q="carol", _user=mock_user)

    assert len(results) == 1
    assert results[0].email == "carol@startup.dev"


@pytest.mark.asyncio
async def test_list_contacts_returns_empty_list_when_no_match():
    """list_contacts() returns an empty list when the query matches nothing."""
    from app.api.routes.crm import list_contacts

    mock_user = MagicMock()
    with patch(
        "app.api.routes.crm.get_crm_client",
        return_value=MockCRM(),
    ):
        results = await list_contacts(q="zzz_no_match_xyz", _user=mock_user)

    assert results == []
