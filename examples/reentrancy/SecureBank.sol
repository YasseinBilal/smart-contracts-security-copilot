// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @notice Secure ETH bank — demonstrates CEI pattern + ReentrancyGuard
contract SecureBank {
    mapping(address => uint256) public balances;
    uint256 public constant WITHDRAWAL_LIMIT = 1 ether;
    bool private _locked;

    modifier nonReentrant() {
        require(!_locked, "Reentrant call");
        _locked = true;
        _;
        _locked = false;
    }

    event Deposit(address indexed user, uint256 amount);
    event Withdrawal(address indexed user, uint256 amount);

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        emit Deposit(msg.sender, msg.value);
    }

    // SECURE: CEI pattern — state updated BEFORE external call
    function withdraw() public nonReentrant {
        uint256 bal = balances[msg.sender];
        require(bal > 0, "No balance to withdraw");
        require(bal <= WITHDRAWAL_LIMIT, "Exceeds withdrawal limit");

        balances[msg.sender] = 0; // Effect first
        emit Withdrawal(msg.sender, bal);

        (bool sent, ) = msg.sender.call{value: bal}(""); // Interaction last
        require(sent, "ETH transfer failed");
    }
}
