import json
import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import get_db


def _make_db_override(mock_db: AsyncMock):
    async def override():
        yield mock_db
    return override


def _make_scan_stats(total=3, avg_critical=1.0, avg_high=0.5, avg_medium=0.0, avg_tokens=800):
    s = MagicMock()
    s.total_scans = total
    s.avg_critical = avg_critical
    s.avg_high = avg_high
    s.avg_medium = avg_medium
    s.avg_tokens = avg_tokens
    return s


def _make_fp_stats(total=10, fp_count=1):
    s = MagicMock()
    s.total = total
    s.fp_count = fp_count
    return s


async def test_eval_returns_expected_shape():
    scan_result = MagicMock()
    scan_result.one.return_value = _make_scan_stats()
    fp_result = MagicMock()
    fp_result.one.return_value = _make_fp_stats()
    latency_result = MagicMock()
    latency_result.scalars.return_value.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[scan_result, fp_result, latency_result])

    app.dependency_overrides[get_db] = _make_db_override(mock_db)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/eval")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert "total_scans" in data
    assert "avg_findings_per_scan" in data
    assert "false_positive_rate_pct" in data
    assert "avg_tokens_per_scan" in data
    assert "avg_node_latencies_sec" in data


async def test_eval_false_positive_rate_calculation():
    scan_result = MagicMock()
    scan_result.one.return_value = _make_scan_stats(total=5)
    fp_result = MagicMock()
    fp_result.one.return_value = _make_fp_stats(total=20, fp_count=4)
    latency_result = MagicMock()
    latency_result.scalars.return_value.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[scan_result, fp_result, latency_result])

    app.dependency_overrides[get_db] = _make_db_override(mock_db)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/eval")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["false_positive_rate_pct"] == 20.0


async def test_eval_parses_node_latencies():
    scan_result = MagicMock()
    scan_result.one.return_value = _make_scan_stats()
    fp_result = MagicMock()
    fp_result.one.return_value = _make_fp_stats()

    latency_rows = [
        json.dumps({"parse": 0.1, "static_scan": 0.5, "ai_reason": 2.3}),
        json.dumps({"parse": 0.2, "static_scan": 0.4, "ai_reason": 1.9}),
    ]
    latency_result = MagicMock()
    latency_result.scalars.return_value.all.return_value = latency_rows

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[scan_result, fp_result, latency_result])

    app.dependency_overrides[get_db] = _make_db_override(mock_db)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/eval")
    finally:
        app.dependency_overrides.clear()

    data = resp.json()
    latencies = data["avg_node_latencies_sec"]
    assert "parse" in latencies
    assert "ai_reason" in latencies
    assert abs(latencies["parse"] - 0.15) < 0.001


async def test_eval_zero_scans_safe():
    scan_result = MagicMock()
    scan_result.one.return_value = _make_scan_stats(
        total=0, avg_critical=None, avg_high=None, avg_medium=None, avg_tokens=None
    )
    fp_result = MagicMock()
    fp_result.one.return_value = _make_fp_stats(total=0, fp_count=0)
    latency_result = MagicMock()
    latency_result.scalars.return_value.all.return_value = []

    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(side_effect=[scan_result, fp_result, latency_result])

    app.dependency_overrides[get_db] = _make_db_override(mock_db)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/eval")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_scans"] == 0
    assert data["false_positive_rate_pct"] == 0.0
