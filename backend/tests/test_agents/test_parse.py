import pytest
from app.agents.nodes.parse import parse_node

SIMPLE_SOURCE = """
pragma solidity ^0.8.0;

contract SimpleBank {
    mapping(address => uint256) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        balances[msg.sender] -= amount;
        payable(msg.sender).transfer(amount);
    }
}
"""


async def test_parse_node_returns_ast():
    state = {"source": SIMPLE_SOURCE, "filename": "SimpleBank.sol", "scan_id": "test-id"}
    result = await parse_node(state)

    assert "ast" in result
    assert isinstance(result["ast"], dict)
    assert "parse_latency" in result
    assert result["parse_latency"] >= 0


async def test_parse_node_extracts_functions_via_fallback():
    state = {"source": SIMPLE_SOURCE, "filename": "SimpleBank.sol", "scan_id": "test-id"}
    result = await parse_node(state)

    ast = result["ast"]
    # Either Slither JSON or basic_ast fallback — both should contain function names
    if "functions" in ast:
        assert "deposit" in ast["functions"]
        assert "withdraw" in ast["functions"]
    if "contracts" in ast:
        assert "SimpleBank" in ast["contracts"]


async def test_parse_node_does_not_crash_on_invalid_source():
    state = {"source": "this is not solidity at all!!!", "filename": "bad.sol", "scan_id": "x"}
    result = await parse_node(state)

    # Should not raise — must return a state dict regardless
    assert "ast" in result
    assert isinstance(result["ast"], dict)


async def test_parse_node_preserves_existing_state_keys():
    state = {
        "source": SIMPLE_SOURCE,
        "filename": "SimpleBank.sol",
        "scan_id": "test-id",
        "extra_key": "preserved",
    }
    result = await parse_node(state)
    assert result["extra_key"] == "preserved"
