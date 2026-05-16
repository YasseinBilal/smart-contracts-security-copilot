// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @notice Deliberately vulnerable signature verifier — signature replay attack
/// Missing: (1) per-address nonce — same signature can be used multiple times
/// Missing: (2) chainId in signed data — cross-chain replay possible
/// Inspired by the Poly Network exploit ($611M, 2021)
contract VulnerableSigVerifier {
    address public owner;

    mapping(address => bool) public authorized;

    event ActionExecuted(address indexed by, bytes32 indexed actionHash);

    constructor() {
        owner = msg.sender;
    }

    /// @notice Execute a privileged action if caller presents a valid owner signature
    /// VULNERABILITY: No nonce — the same (hash, sig) pair can be replayed indefinitely
    /// VULNERABILITY: No chainId — valid on any chain with the same contract address
    function executeWithSignature(
        bytes32 actionHash,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        // Reconstruct the signed message — but no nonce or chainId!
        bytes32 messageHash = keccak256(
            abi.encodePacked("\x19Ethereum Signed Message:\n32", actionHash)
        );

        address signer = ecrecover(messageHash, v, r, s);
        require(signer == owner, "Not authorized");

        // No nonce consumed — anyone who saw this signature can replay it
        authorized[msg.sender] = true;
        emit ActionExecuted(msg.sender, actionHash);
    }
}
