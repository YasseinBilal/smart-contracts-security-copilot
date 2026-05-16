import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import get_db

_NOW = datetime(2024, 1, 15, 12, 0, 0)


def _mock_scan(scan_id="scan-1", filename="Test.sol", status="completed"):
    s = MagicMock()
    s.id = scan_id
    s.filename = filename
    s.status = status
    s.triggered_by = "manual"
    s.critical_count = 1
    s.high_count = 0
    s.medium_count = 0
    s.low_count = 0
    s.info_count = 0
    s.total_tokens = 500
    s.created_at = _NOW
    s.completed_at = _NOW
    s.findings = []
    s.node_latencies = None
    s.explanation = None
    return s


def _make_db_override(mock_db: AsyncMock):
    async def override():
        yield mock_db
    return override


async def test_list_scans_returns_empty():
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_db] = _make_db_override(mock_db)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/scans")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_scans_returns_scan_list():
    scan = _mock_scan()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [scan]
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_db] = _make_db_override(mock_db)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/scans")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["id"] == "scan-1"
    assert data[0]["status"] == "completed"


async def test_get_scan_not_found():
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_db] = _make_db_override(mock_db)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/scans/nonexistent-id")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Scan not found"


async def test_get_scan_returns_detail():
    scan = _mock_scan(scan_id="abc-123", filename="VulnBank.sol")
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = scan
    mock_db = AsyncMock()
    mock_db.execute = AsyncMock(return_value=mock_result)

    app.dependency_overrides[get_db] = _make_db_override(mock_db)
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/api/scans/abc-123")
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "abc-123"
    assert data["filename"] == "VulnBank.sol"
    assert "findings" in data
