import pytest
from app.detectors.reentrancy import ReentrancyDetector

VULNERABLE_SOURCE = """
pragma solidity ^0.8.0;

contract VulnerableBank {
    mapping(address => uint256) public balances;

    function deposit() public payable {
        balances[msg.sender] += msg.value;
    }

    function withdraw() public {
        uint256 bal = balances[msg.sender];
        require(bal > 0, "No balance");
        // Interaction BEFORE effect — CEI violation
        (bool sent, ) = msg.sender.call{value: bal}("");
        require(sent, "Failed");
        balances[msg.sender] = 0;  // state write AFTER external call
    }
}
"""

SAFE_SOURCE = """
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

contract SafeBank is ReentrancyGuard {
    mapping(address => uint256) public balances;

    function withdraw() public nonReentrant {
        uint256 bal = balances[msg.sender];
        require(bal > 0);
        balances[msg.sender] = 0;  // effect BEFORE interaction
        (bool sent, ) = msg.sender.call{value: bal}("");
        require(sent);
    }
}
"""

SAFE_CEI_SOURCE = """
pragma solidity ^0.8.0;

contract SafeBankCEI {
    mapping(address => uint256) public balances;

    function withdraw() public {
        uint256 bal = balances[msg.sender];
        require(bal > 0);
        balances[msg.sender] = 0;  // effect first
        (bool sent, ) = msg.sender.call{value: bal}("");
        require(sent);
    }
}
"""


def test_detects_cei_violation():
    detector = ReentrancyDetector()
    findings = detector.detect(VULNERABLE_SOURCE, "VulnerableBank.sol")
    assert len(findings) >= 1
    assert findings[0].category == "REENTRANCY"
    assert findings[0].severity == "CRITICAL"


def test_no_false_positive_nonreentrant():
    detector = ReentrancyDetector()
    findings = detector.detect(SAFE_SOURCE, "SafeBank.sol")
    assert len(findings) == 0


def test_no_false_positive_cei():
    detector = ReentrancyDetector()
    findings = detector.detect(SAFE_CEI_SOURCE, "SafeBankCEI.sol")
    assert len(findings) == 0
