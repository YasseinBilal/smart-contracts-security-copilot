// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @notice Deliberately vulnerable ETH bank — demonstrates reentrancy (CEI violation)
/// This mimics the pattern exploited in The DAO hack ($60M, 2016).
/// The withdrawal limit does NOT prevent reentrancy — it is also bypassed per reentry.
contract VulnerableBank {
    mapping(address => uint256) public balances;
    uint256 public constant WITHDRAWAL_LIMIT = 1 ether;

    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    // VULNERABILITY: External call before state update (CEI violation)
    // 1. Balance is checked (Checks) ✓
    // 2. ETH is sent to caller (Interaction) — attacker's receive() re-enters here
    // 3. Balance is zeroed (Effects) — too late, already drained
    function withdraw() public {
        uint256 bal = balances[msg.sender];
        require(bal > 0, "No balance to withdraw");
        require(bal <= WITHDRAWAL_LIMIT, "Exceeds withdrawal limit");

        // DANGER: External call before state update
        (bool sent, ) = msg.sender.call{value: bal}("");
        require(sent, "ETH transfer failed");

        balances[msg.sender] = 0; // State updated AFTER interaction — too late
        emit Withdrawal(msg.sender, bal);
    }

    function getBalance() public view returns (uint256) {
        return address(this).balance;
    }
}
