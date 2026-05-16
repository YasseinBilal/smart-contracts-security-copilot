import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import app

SIMPLE_SOURCE = """
pragma solidity ^0.8.0;
contract SimpleBank {
    address public owner;
    constructor() { owner = msg.sender; }
    function withdraw(uint256 amount) public {
        require(msg.sender == owner);
        payable(msg.sender).transfer(amount);
    }
}
"""

MOCK_EXPLAIN_RESPONSE = {
    "summary": "SimpleBank holds ETH and allows the owner to withdraw funds.",
    "privileged_functions": ["withdraw"],
    "trust_assumptions": ["Only the deployer can withdraw funds."],
}


async def test_explain_returns_summary():
    with patch("app.routers.explain.chat_json", new=AsyncMock(return_value=(MOCK_EXPLAIN_RESPONSE, 300))):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/explain", json={"source": SIMPLE_SOURCE, "filename": "SimpleBank.sol"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["filename"] == "SimpleBank.sol"
    assert "SimpleBank" in data["summary"]
    assert "withdraw" in data["privileged_functions"]


async def test_explain_returns_trust_assumptions():
    with patch("app.routers.explain.chat_json", new=AsyncMock(return_value=(MOCK_EXPLAIN_RESPONSE, 300))):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/explain", json={"source": SIMPLE_SOURCE})

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["trust_assumptions"]) >= 1


async def test_explain_missing_source_rejected():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/explain", json={"filename": "X.sol"})

    assert resp.status_code == 422


async def test_explain_default_filename():
    with patch("app.routers.explain.chat_json", new=AsyncMock(return_value=(MOCK_EXPLAIN_RESPONSE, 100))):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/api/explain", json={"source": SIMPLE_SOURCE})

    assert resp.status_code == 200
    assert resp.json()["filename"] == "contract.sol"
