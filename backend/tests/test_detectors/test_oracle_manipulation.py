import pytest
from app.detectors.oracle_manipulation import OracleManipulationDetector

VULNERABLE_SOURCE = """
pragma solidity ^0.8.0;

interface IUniswapV2Pair {
    function getReserves() external view returns (uint112, uint112, uint32);
}

contract SpotPriceOracle {
    IUniswapV2Pair public pair;

    function getPrice() public view returns (uint256) {
        (uint112 reserve0, uint112 reserve1, ) = pair.getReserves();
        return uint256(reserve0) * 1e18 / uint256(reserve1);
    }

    function borrow(uint256 amount) public {
        require(getPrice() >= 1e18, "Price too low");
        // ... lend against this spot price
    }
}
"""

SAFE_TWAP_SOURCE = """
pragma solidity ^0.8.0;

interface IUniswapV2Pair {
    function getReserves() external view returns (uint112, uint112, uint32);
    function price0CumulativeLast() external view returns (uint256);
    function blockTimestampLast() external view returns (uint32);
}

contract SafeTWAPOracle {
    IUniswapV2Pair public pair;
    uint256 public price0CumulativeLast;
    uint32 public blockTimestampLast;

    function consult() public view returns (uint256) {
        uint256 price0Cumulative = pair.price0CumulativeLast();
        // TWAP calculation using blockTimestampLast
        return price0Cumulative;
    }
}
"""


def test_detects_spot_price():
    detector = OracleManipulationDetector()
    findings = detector.detect(VULNERABLE_SOURCE, "SpotPriceOracle.sol")
    assert len(findings) >= 1
    assert findings[0].category == "ORACLE_MANIPULATION"
    assert findings[0].severity == "HIGH"


def test_no_false_positive_twap():
    detector = OracleManipulationDetector()
    findings = detector.detect(SAFE_TWAP_SOURCE, "SafeTWAP.sol")
    assert len(findings) == 0
