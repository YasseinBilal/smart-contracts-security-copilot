// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @notice Deliberately vulnerable lending pool — spot price oracle manipulation
/// Mimics the pattern exploited by bZx ($1M, 2020) and Cream Finance ($130M, 2021).
/// An attacker can:
/// 1. Take a flash loan of token A
/// 2. Dump token A into the Uniswap V2 pair, collapsing its price
/// 3. Borrow against the artificially low collateral valuation
/// 4. Repay flash loan, keep the profit
interface IUniswapV2Pair {
    function getReserves() external view returns (uint112 reserve0, uint112 reserve1, uint32 blockTimestampLast);
    function token0() external view returns (address);
    function token1() external view returns (address);
}

interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

contract VulnerableLendingPool {
    IUniswapV2Pair public immutable pair;
    IERC20 public immutable collateralToken;
    IERC20 public immutable borrowToken;

    mapping(address => uint256) public collateralDeposited;
    mapping(address => uint256) public borrowedAmount;

    uint256 public constant COLLATERAL_RATIO = 150; // 150% collateral required

    constructor(address _pair, address _collateral, address _borrow) {
        pair = IUniswapV2Pair(_pair);
        collateralToken = IERC20(_collateral);
        borrowToken = IERC20(_borrow);
    }

    // VULNERABILITY: Uses spot price from Uniswap V2 as collateral value
    // This price is manipulable within a single transaction via flash loan
    function getCollateralPrice() public view returns (uint256 price) {
        (uint112 reserve0, uint112 reserve1, ) = pair.getReserves();
        // Spot price: reserve ratio — can be moved to any value intra-block
        if (pair.token0() == address(collateralToken)) {
            price = uint256(reserve1) * 1e18 / uint256(reserve0);
        } else {
            price = uint256(reserve0) * 1e18 / uint256(reserve1);
        }
    }

    function depositCollateral(uint256 amount) external {
        collateralToken.transferFrom(msg.sender, address(this), amount);
        collateralDeposited[msg.sender] += amount;
    }

    function borrow(uint256 borrowAmount) external {
        uint256 price = getCollateralPrice();
        uint256 collateralValue = collateralDeposited[msg.sender] * price / 1e18;
        uint256 maxBorrow = collateralValue * 100 / COLLATERAL_RATIO;

        require(borrowedAmount[msg.sender] + borrowAmount <= maxBorrow, "Undercollateralized");
        borrowedAmount[msg.sender] += borrowAmount;
        borrowToken.transfer(msg.sender, borrowAmount);
    }
}
