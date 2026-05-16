import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.database import get_db

SIMPLE_SOURCE = "pragma solidity ^0.8.0;\ncontract X {}"

MOCK_REPORT = {
    "findings": [],
    "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
    "node_latencies": {"parse": 0.1, "static_scan": 0.2},
    "explanation": "A minimal empty contract.",
    "total_tokens": 300,
}


def _make_db_override(mock_db: AsyncMock):
    async def override():
        yield mock_db
    return override


def _parse_sse(text: str) -> list[dict]:
    events = []
    for line in text.splitlines():
        if line.startswith("data: "):
            try:
                events.append(json.loads(line[6:]))
            except json.JSONDecodeError:
                pass
    return events


async def _mock_astream(initial_state, stream_mode=None):
    yield {"parse": {"ast": {}, "parse_latency": 0.1}}
    yield {"static_scan": {"static_findings": [], "static_latency": 0.2}}
    yield {"memory_query": {"rag_context": []}}
    yield {"ai_reason": {"ai_findings": [], "total_tokens": 100}}
    yield {"test_gen": {"test_stubs": {}}}
    yield {"explain": {"explanation": "A minimal empty contract.", "total_tokens": 200}}
    yield {"report": {"report": MOCK_REPORT, "total_tokens": 300}}


def _make_mock_db():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.get = AsyncMock(return_value=MagicMock())
    return mock_db


async def test_analyze_streams_sse_events():
    mock_db = _make_mock_db()
    app.dependency_overrides[get_db] = _make_db_override(mock_db)
    try:
        with (
            patch("app.routers.analyze.audit_workflow") as mock_workflow,
            patch("app.routers.analyze._persist", new=AsyncMock()),
        ):
            mock_workflow.astream = _mock_astream

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    "/api/analyze",
                    json={"source": SIMPLE_SOURCE, "filename": "X.sol"},
                )
    finally:
        app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]

    events = _parse_sse(resp.text)
    stages = [e["stage"] for e in events]
    assert "parsing" in stages
    assert "done" in stages


async def test_analyze_done_event_contains_scan_id():
    mock_db = _make_mock_db()
    app.dependency_overrides[get_db] = _make_db_override(mock_db)
    try:
        with (
            patch("app.routers.analyze.audit_workflow") as mock_workflow,
            patch("app.routers.analyze._persist", new=AsyncMock()),
        ):
            mock_workflow.astream = _mock_astream

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    "/api/analyze",
                    json={"source": SIMPLE_SOURCE, "filename": "X.sol"},
                )
    finally:
        app.dependency_overrides.clear()

    events = _parse_sse(resp.text)
    done_events = [e for e in events if e.get("stage") == "done"]
    assert len(done_events) == 1
    assert "scan_id" in done_events[0]
    assert "report" in done_events[0]


async def test_analyze_missing_source_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/analyze", json={"filename": "X.sol"})

    assert resp.status_code == 422


async def test_analyze_workflow_error_yields_error_event():
    async def _failing_astream(initial_state, stream_mode=None):
        raise RuntimeError("Simulated workflow failure")
        yield  # make it an async generator

    mock_db = _make_mock_db()
    app.dependency_overrides[get_db] = _make_db_override(mock_db)
    try:
        with patch("app.routers.analyze.audit_workflow") as mock_workflow:
            mock_workflow.astream = _failing_astream

            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post(
                    "/api/analyze",
                    json={"source": SIMPLE_SOURCE, "filename": "X.sol"},
                )
    finally:
        app.dependency_overrides.clear()

    events = _parse_sse(resp.text)
    error_events = [e for e in events if e.get("stage") == "error"]
    assert len(error_events) == 1
    assert "Simulated workflow failure" in error_events[0]["message"]
