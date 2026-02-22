"""Unit tests for trace_service module."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.email import EmailClassification, EmailStatus
from tests.services.conftest import make_agent_log, make_email, make_tool_execution


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
# list_traces()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_traces_returns_empty_when_no_emails(mock_db):
    """list_traces() returns an empty list when the user has no emails."""
    from app.services.trace_service import list_traces

    mock_db.execute = AsyncMock(return_value=_scalars_all([]))

    traces, total = await list_traces(mock_db, uuid.uuid4())

    assert traces == []
    assert total == 0


@pytest.mark.asyncio
async def test_list_traces_aggregates_steps_by_trace(mock_db):
    """list_traces() groups agent logs by trace_id and sums latency."""
    from app.services.trace_service import list_traces

    user_id = uuid.uuid4()
    email = make_email(user_id=user_id)
    trace_id = uuid.uuid4()

    log1 = make_agent_log(email_id=email.id, trace_id=trace_id, latency_ms=100.0)
    log2 = make_agent_log(
        email_id=email.id,
        trace_id=trace_id,
        step_name="retrieve",
        step_order=1,
        latency_ms=200.0,
    )

    # First execute = user emails, second = agent logs.
    mock_db.execute = AsyncMock(
        side_effect=[
            _scalars_all([email]),
            _scalars_all([log1, log2]),
        ]
    )

    traces, total = await list_traces(mock_db, user_id)

    assert len(traces) == 1
    trace = traces[0]
    assert trace["trace_id"] == trace_id
    assert trace["total_latency_ms"] == 300.0
    assert trace["step_count"] == 2
    assert trace["status"] == "completed"
    assert trace["email_subject"] == email.subject


@pytest.mark.asyncio
async def test_list_traces_marks_failed_on_error_step(mock_db):
    """list_traces() marks a trace 'failed' when any step has an error_message."""
    from app.services.trace_service import list_traces

    user_id = uuid.uuid4()
    email = make_email(user_id=user_id)
    trace_id = uuid.uuid4()

    log = make_agent_log(
        email_id=email.id,
        trace_id=trace_id,
        error_message="something went wrong",
    )

    mock_db.execute = AsyncMock(
        side_effect=[
            _scalars_all([email]),
            _scalars_all([log]),
        ]
    )

    traces, total = await list_traces(mock_db, user_id)

    assert traces[0]["status"] == "failed"


@pytest.mark.asyncio
async def test_list_traces_respects_limit_and_offset(mock_db):
    """list_traces() honours the limit and offset pagination parameters."""
    from app.services.trace_service import list_traces

    user_id = uuid.uuid4()

    # Create 5 distinct emails and traces — one trace per email.
    emails = [make_email(user_id=user_id, gmail_id=f"gmail-{i}") for i in range(5)]
    trace_ids = [uuid.uuid4() for _ in range(5)]
    logs = [
        make_agent_log(email_id=emails[i].id, trace_id=trace_ids[i])
        for i in range(5)
    ]

    mock_db.execute = AsyncMock(
        side_effect=[
            _scalars_all(emails),
            _scalars_all(logs),
        ]
    )

    traces, total = await list_traces(mock_db, user_id, limit=2, offset=0)

    assert len(traces) == 2


# ---------------------------------------------------------------------------
# get_trace_detail()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_trace_detail_returns_full_trace(mock_db):
    """get_trace_detail() returns all steps and tool executions for a trace."""
    from app.services.trace_service import get_trace_detail

    email = make_email()
    trace_id = uuid.uuid4()

    te = make_tool_execution()
    log = make_agent_log(
        email_id=email.id,
        trace_id=trace_id,
        latency_ms=150.0,
        input_state={"key": "val"},
        output_state={"result": "ok"},
    )
    log.tool_executions = [te]

    # First execute = agent logs with selectinload, second = email.
    mock_db.execute = AsyncMock(
        side_effect=[
            _scalars_all([log]),
            _scalars_first(email),
        ]
    )

    result = await get_trace_detail(mock_db, trace_id)

    assert result["trace_id"] == trace_id
    assert result["total_latency_ms"] == 150.0
    assert len(result["steps"]) == 1
    step = result["steps"][0]
    assert step["step_name"] == log.step_name
    assert len(step["tool_executions"]) == 1
    assert step["tool_executions"][0]["tool_name"] == te.tool_name


@pytest.mark.asyncio
async def test_get_trace_detail_raises_404_when_not_found(mock_db):
    """get_trace_detail() raises HTTP 404 when no logs exist for the trace_id."""
    from fastapi import HTTPException

    from app.services.trace_service import get_trace_detail

    mock_db.execute = AsyncMock(return_value=_scalars_all([]))

    with pytest.raises(HTTPException) as exc_info:
        await get_trace_detail(mock_db, uuid.uuid4())

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_trace_detail_handles_missing_email(mock_db):
    """get_trace_detail() returns an empty email summary when email is deleted."""
    from app.services.trace_service import get_trace_detail

    trace_id = uuid.uuid4()
    log = make_agent_log(trace_id=trace_id, latency_ms=50.0)

    mock_db.execute = AsyncMock(
        side_effect=[
            _scalars_all([log]),
            _scalars_first(None),  # email has been deleted
        ]
    )

    result = await get_trace_detail(mock_db, trace_id)

    assert result["email"] == {}
    assert result["total_latency_ms"] == 50.0
