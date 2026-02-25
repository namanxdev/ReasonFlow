"""Unit tests for metrics_service module."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.models.email import EmailClassification
from tests.services.conftest import make_agent_log, make_email, make_tool_execution

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _scalars_all(items):
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = items
    result_mock = MagicMock()
    result_mock.scalars.return_value = scalars_mock
    return result_mock


def _rows(pairs: list[tuple]):
    """Mock db.execute() result for GROUP BY queries that return (col, count) rows."""
    result_mock = MagicMock()
    result_mock.all.return_value = pairs
    execute_result = AsyncMock()
    execute_result.__await__ = lambda self: iter([result_mock])

    async def awaitable():
        return result_mock

    return awaitable()


# ---------------------------------------------------------------------------
# _compute_percentiles() — private helper
# ---------------------------------------------------------------------------


def test_compute_percentiles_empty_list():
    from app.services.metrics_service import _compute_percentiles

    result = _compute_percentiles([])
    assert result == {"p50": 0.0, "p90": 0.0, "p99": 0.0, "mean": 0.0, "min": 0.0, "max": 0.0}


def test_compute_percentiles_single_value():
    from app.services.metrics_service import _compute_percentiles

    result = _compute_percentiles([200.0])
    assert result["p50"] == 200.0
    assert result["p99"] == 200.0
    assert result["mean"] == 200.0
    assert result["min"] == 200.0
    assert result["max"] == 200.0


def test_compute_percentiles_multiple_values():
    from app.services.metrics_service import _compute_percentiles

    values = [100.0, 200.0, 300.0, 400.0, 500.0]
    result = _compute_percentiles(values)
    # Sorted: [100, 200, 300, 400, 500]; p50 rank = int(50/100*5)=2 → index 1 → 200
    assert result["p50"] == 200.0
    assert result["min"] == 100.0
    assert result["max"] == 500.0
    assert result["mean"] == 300.0


# ---------------------------------------------------------------------------
# get_intent_distribution()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_intent_distribution_returns_buckets(mock_db):
    """get_intent_distribution() computes percentage correctly."""
    from app.services.metrics_service import get_intent_distribution

    user_id = uuid.uuid4()
    rows = [
        (EmailClassification.INQUIRY, 3),
        (EmailClassification.SPAM, 1),
    ]
    result_mock = MagicMock()
    result_mock.all.return_value = rows
    mock_db.execute = AsyncMock(return_value=result_mock)

    result = await get_intent_distribution(mock_db, user_id, None, None)

    assert result["total"] == 4
    buckets = {b["classification"]: b for b in result["buckets"]}
    assert buckets[EmailClassification.INQUIRY]["count"] == 3
    assert buckets[EmailClassification.INQUIRY]["percentage"] == 75.0
    assert buckets[EmailClassification.SPAM]["percentage"] == 25.0


@pytest.mark.asyncio
async def test_get_intent_distribution_empty(mock_db):
    """get_intent_distribution() handles zero emails gracefully."""
    from app.services.metrics_service import get_intent_distribution

    result_mock = MagicMock()
    result_mock.all.return_value = []
    mock_db.execute = AsyncMock(return_value=result_mock)

    result = await get_intent_distribution(mock_db, uuid.uuid4(), None, None)

    assert result["total"] == 0
    assert result["buckets"] == []


@pytest.mark.asyncio
async def test_get_intent_distribution_with_date_range(mock_db):
    """get_intent_distribution() passes date range filters to the query."""
    from app.services.metrics_service import get_intent_distribution

    result_mock = MagicMock()
    result_mock.all.return_value = []
    mock_db.execute = AsyncMock(return_value=result_mock)

    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 31, tzinfo=UTC)

    result = await get_intent_distribution(mock_db, uuid.uuid4(), start, end)

    assert result["start"] == start
    assert result["end"] == end


# ---------------------------------------------------------------------------
# get_latency_metrics()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_latency_metrics_returns_zero_when_no_logs(mock_db):
    """get_latency_metrics() returns zero stats when there are no agent logs."""
    from app.services.metrics_service import get_latency_metrics

    mock_db.execute = AsyncMock(return_value=_scalars_all([]))

    result = await get_latency_metrics(mock_db, uuid.uuid4(), None, None)

    assert result["sample_count"] == 0
    assert result["overall"]["mean"] == 0.0
    assert result["by_step"] == {}


@pytest.mark.asyncio
async def test_get_latency_metrics_aggregates_traces(mock_db):
    """get_latency_metrics() sums step latencies per trace and computes stats."""
    from app.services.metrics_service import get_latency_metrics

    user_id = uuid.uuid4()
    email = make_email(user_id=user_id)
    email_id = email.id
    trace_id_a = uuid.uuid4()
    trace_id_b = uuid.uuid4()

    logs = [
        make_agent_log(email_id=email_id, trace_id=trace_id_a, latency_ms=100.0),
        make_agent_log(
            email_id=email_id,
            trace_id=trace_id_a,
            step_name="retrieve",
            step_order=1,
            latency_ms=200.0,
        ),
        make_agent_log(email_id=email_id, trace_id=trace_id_b, latency_ms=50.0),
    ]

    mock_db.execute = AsyncMock(return_value=_scalars_all(logs))

    result = await get_latency_metrics(mock_db, user_id, None, None)

    # Two unique traces: 300 ms and 50 ms.
    assert result["sample_count"] == 2
    assert result["overall"]["min"] == 50.0
    assert result["overall"]["max"] == 300.0
    assert "classify" in result["by_step"]
    assert "retrieve" in result["by_step"]


# ---------------------------------------------------------------------------
# get_tool_metrics()
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_tool_metrics_returns_empty_when_no_executions(mock_db):
    """get_tool_metrics() returns an empty tools list when there are none."""
    from app.services.metrics_service import get_tool_metrics

    mock_db.execute = AsyncMock(return_value=_scalars_all([]))

    result = await get_tool_metrics(mock_db, uuid.uuid4(), None, None)

    assert result["tools"] == []


@pytest.mark.asyncio
async def test_get_tool_metrics_computes_success_rates(mock_db):
    """get_tool_metrics() calculates success rate and mean latency per tool."""
    from app.services.metrics_service import get_tool_metrics

    executions = [
        make_tool_execution(tool_name="search", success=True, latency_ms=40.0),
        make_tool_execution(tool_name="search", success=True, latency_ms=60.0),
        make_tool_execution(tool_name="search", success=False, latency_ms=10.0),
        make_tool_execution(tool_name="calendar", success=True, latency_ms=80.0),
    ]

    mock_db.execute = AsyncMock(return_value=_scalars_all(executions))

    result = await get_tool_metrics(mock_db, uuid.uuid4(), None, None)

    tools = {t["tool_name"]: t for t in result["tools"]}
    assert tools["search"]["total_calls"] == 3
    assert tools["search"]["successful_calls"] == 2
    assert tools["search"]["failed_calls"] == 1
    assert round(tools["search"]["success_rate"], 4) == round(2 / 3, 4)
    assert tools["calendar"]["success_rate"] == 1.0
