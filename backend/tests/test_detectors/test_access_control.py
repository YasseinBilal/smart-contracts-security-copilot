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
