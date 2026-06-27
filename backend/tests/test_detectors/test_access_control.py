import pytest
from app.detectors.access_control import AccessControlDetector

VULNERABLE_SOURCE = """
pragma solidity ^0.8.0;

contract UnprotectedMint {
    mapping(address => uint256) public balances;
    uint256 public totalSupply;

    function mint(address to, uint256 amount) public {
        balances[to] += amount;
        totalSupply += amount;
    }
}
"""

SAFE_SOURCE = """
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/access/Ownable.sol";

contract ProtectedMint is Ownable {
    mapping(address => uint256) public balances;

    function mint(address to, uint256 amount) public onlyOwner {
        balances[to] += amount;
    }
}
"""

SAFE_REQUIRE_SOURCE = """
pragma solidity ^0.8.0;

contract ProtectedWithRequire {
    address public owner;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function mint(address to, uint256 amount) public {
        require(msg.sender == owner, "Not owner");
        balances[to] += amount;
    }
}
"""


WITHDRAW_WITH_BALANCE_CHECK_SOURCE = """
pragma solidity ^0.8.0;

contract VulnerableVault {
    mapping(address => uint256) public balances;
    address public owner;
    bool public paused;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        (bool sent, ) = msg.sender.call{value: amount}("");
        require(sent, "Transfer failed");
        balances[msg.sender] -= amount;
    }

    function setPaused(bool _paused) public {
        paused = _paused;
    }

    function emergencyWithdraw() public {
        payable(msg.sender).transfer(address(this).balance);
    }
}
"""


def test_no_false_positive_user_withdraw_with_balance_check():
    detector = AccessControlDetector()
    findings = detector.detect(WITHDRAW_WITH_BALANCE_CHECK_SOURCE, "VulnerableVault.sol")
    titles = [f.title for f in findings]
    # withdraw() is user-facing (guarded by balances[msg.sender]) — must NOT be flagged
    assert not any("withdraw()" in t for t in titles), (
        f"withdraw() with balance check was incorrectly flagged: {titles}"
    )
    # setPaused() changes global state — must be flagged
    assert any("setPaused" in t for t in titles), (
        f"setPaused() was not flagged: {titles}"
    )
    # emergencyWithdraw() has no user-balance guard — must still be flagged
    assert any("emergencyWithdraw" in t for t in titles), (
        f"emergencyWithdraw() was not flagged: {titles}"
    )


def test_detects_unprotected_mint():
    detector = AccessControlDetector()
    findings = detector.detect(VULNERABLE_SOURCE, "UnprotectedMint.sol")
    assert len(findings) >= 1
    assert findings[0].category == "ACCESS_CONTROL"
    assert findings[0].severity == "HIGH"


def test_no_false_positive_onlyowner():
    detector = AccessControlDetector()
    findings = detector.detect(SAFE_SOURCE, "ProtectedMint.sol")
    assert len(findings) == 0


def test_no_false_positive_require():
    detector = AccessControlDetector()
    findings = detector.detect(SAFE_REQUIRE_SOURCE, "ProtectedWithRequire.sol")
    assert len(findings) == 0
