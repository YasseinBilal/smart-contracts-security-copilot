import pytest
from app.agents.nodes.static_scan import static_scan_node

VULNERABLE_SOURCE = """
pragma solidity ^0.8.0;
contract VulnBank {
    mapping(address => uint256) public balances;
    function deposit() public payable { balances[msg.sender] += msg.value; }
    function withdraw() public {
        uint256 bal = balances[msg.sender];
        require(bal > 0);
        (bool sent, ) = msg.sender.call{value: bal}("");
        require(sent);
        balances[msg.sender] = 0;
    }
}
"""

SAFE_SOURCE = """
pragma solidity ^0.8.0;
contract SafeBank {
    mapping(address => uint256) public balances;
    bool private locked;
    modifier nonReentrant() {
        require(!locked);
        locked = true;
        _;
        locked = false;
    }
    function withdraw() public nonReentrant {
        uint256 bal = balances[msg.sender];
        require(bal > 0);
        balances[msg.sender] = 0;
        (bool sent, ) = msg.sender.call{value: bal}("");
        require(sent);
    }
}
"""


async def test_static_scan_finds_reentrancy():
    state = {
        "source": VULNERABLE_SOURCE,
        "filename": "VulnBank.sol",
        "scan_id": "test",
        "ast": {},
    }
    result = await static_scan_node(state)

    assert "static_findings" in result
    findings = result["static_findings"]
    assert len(findings) >= 1
    categories = [f["category"] for f in findings]
    assert "REENTRANCY" in categories


async def test_static_scan_no_false_positive_on_safe_contract():
    state = {
        "source": SAFE_SOURCE,
        "filename": "SafeBank.sol",
        "scan_id": "test",
        "ast": {},
    }
    result = await static_scan_node(state)

    reentrancy_findings = [
        f for f in result["static_findings"] if f["category"] == "REENTRANCY"
    ]
    assert len(reentrancy_findings) == 0


async def test_static_scan_findings_are_serialisable_dicts():
    state = {"source": VULNERABLE_SOURCE, "filename": "VulnBank.sol", "scan_id": "t", "ast": {}}
    result = await static_scan_node(state)

    import json
    # Must not raise — findings go into SSE stream as JSON
    json.dumps(result["static_findings"])


async def test_static_scan_records_latency():
    state = {"source": VULNERABLE_SOURCE, "filename": "VulnBank.sol", "scan_id": "t", "ast": {}}
    result = await static_scan_node(state)
    assert result["static_latency"] >= 0
