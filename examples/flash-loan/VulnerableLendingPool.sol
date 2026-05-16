// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @notice Deliberately vulnerable flash loan pool — missing caller verification in callback
/// The onFlashLoan() callback does not verify msg.sender is the trusted pool.
/// An attacker can call onFlashLoan() directly without taking an actual flash loan,
/// triggering the post-loan logic (e.g., minting reward tokens) without repayment.
interface IERC20 {
    function transfer(address to, uint256 amount) external returns (bool);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
}

interface IFlashLoanReceiver {
    function onFlashLoan(address initiator, address token, uint256 amount, uint256 fee, bytes calldata data) external returns (bytes32);
}

contract VulnerableFlashLoanPool {
    IERC20 public immutable token;
    IERC20 public immutable rewardToken;
    uint256 public constant FEE_BPS = 9; // 0.09%

    event FlashLoan(address indexed receiver, uint256 amount, uint256 fee);

    bytes32 public constant CALLBACK_SUCCESS = keccak256("ERC3156FlashBorrower.onFlashLoan");

    constructor(address _token, address _rewardToken) {
        token = IERC20(_token);
        rewardToken = IERC20(_rewardToken);
    }

    function flashLoan(
        IFlashLoanReceiver receiver,
        uint256 amount,
        bytes calldata data
    ) external returns (bool) {
        uint256 balanceBefore = token.balanceOf(address(this));
        require(balanceBefore >= amount, "Insufficient liquidity");

        uint256 fee = amount * FEE_BPS / 10000;
        token.transfer(address(receiver), amount);

        require(
            receiver.onFlashLoan(msg.sender, address(token), amount, fee, data) == CALLBACK_SUCCESS,
            "Callback failed"
        );

        require(token.balanceOf(address(this)) >= balanceBefore + fee, "Flash loan not repaid");
        emit FlashLoan(address(receiver), amount, fee);
        return true;
    }
}

/// @notice The borrower contract — missing msg.sender check in onFlashLoan
contract VulnerableBorrower is IFlashLoanReceiver {
    VulnerableFlashLoanPool public pool;
    IERC20 public rewardToken;

    constructor(address _pool, address _reward) {
        pool = VulnerableFlashLoanPool(_pool);
        rewardToken = IERC20(_reward);
    }

    // VULNERABILITY: No require(msg.sender == address(pool))
    // Anyone can call this directly and receive rewards without taking a flash loan
    function onFlashLoan(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external override returns (bytes32) {
        // Missing: require(msg.sender == address(pool), "Untrusted caller");

        // Reward logic executes unconditionally — attacker gets rewards for free
        rewardToken.transfer(initiator, 100 ether);

        // Repay (in a real attack, this step is skipped since caller is not the pool)
        IERC20(token).transfer(msg.sender, amount + fee);

        return keccak256("ERC3156FlashBorrower.onFlashLoan");
    }
}
