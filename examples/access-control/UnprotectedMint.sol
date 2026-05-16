// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @notice Deliberately vulnerable token — unprotected mint function
/// Mimics the Parity pattern: initialize() / mint() without access control
/// Any address can call mint() and give themselves unlimited tokens
contract UnprotectedMint {
    string public name = "Vulnerable Token";
    string public symbol = "VULN";
    uint8 public decimals = 18;

    mapping(address => uint256) public balanceOf;
    uint256 public totalSupply;

    address public owner;

    event Transfer(address indexed from, address indexed to, uint256 value);

    // VULNERABILITY: initialize() can be called by anyone — Parity pattern
    function initialize(address _owner) external {
        owner = _owner; // No check if already initialized!
    }

    // VULNERABILITY: mint() is public with no access control
    function mint(address to, uint256 amount) public {
        // Missing: require(msg.sender == owner, "Not owner");
        balanceOf[to] += amount;
        totalSupply += amount;
        emit Transfer(address(0), to, amount);
    }

    function transfer(address to, uint256 amount) external returns (bool) {
        require(balanceOf[msg.sender] >= amount, "Insufficient balance");
        balanceOf[msg.sender] -= amount;
        balanceOf[to] += amount;
        emit Transfer(msg.sender, to, amount);
        return true;
    }
}
