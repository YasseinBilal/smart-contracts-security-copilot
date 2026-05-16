import pytest
from app.detectors.signature_replay import SignatureReplayDetector

VULNERABLE_SOURCE = """
pragma solidity ^0.8.0;

contract VulnerableSigVerifier {
    function execute(bytes32 hash, bytes memory signature) public {
        bytes32 r;
        bytes32 s;
        uint8 v;
        assembly {
            r := mload(add(signature, 32))
            s := mload(add(signature, 64))
            v := byte(0, mload(add(signature, 96)))
        }
        address signer = ecrecover(hash, v, r, s);
        require(signer == owner, "Not authorized");
        // Execute privileged action — no nonce, no chainId
    }

    address public owner;
}
"""

SAFE_SOURCE = """
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/utils/cryptography/EIP712.sol";
import "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";

contract SafeSigVerifier is EIP712 {
    mapping(address => uint256) public nonces;

    constructor() EIP712("SafeSig", "1") {}

    function execute(address user, uint256 nonce, bytes memory signature) public {
        bytes32 digest = _hashTypedDataV4(keccak256(abi.encode(
            keccak256("Execute(address user,uint256 nonce)"),
            user,
            nonce
        )));
        address signer = ECDSA.recover(digest, signature);
        require(signer == user, "Invalid signature");
        require(nonces[user]++ == nonce, "Invalid nonce");
    }
}
"""


def test_detects_missing_nonce_and_chain_id():
    detector = SignatureReplayDetector()
    findings = detector.detect(VULNERABLE_SOURCE, "VulnerableSigVerifier.sol")
    assert len(findings) >= 1
    assert findings[0].category == "SIGNATURE_REPLAY"
    assert findings[0].severity == "HIGH"


def test_no_false_positive_eip712():
    detector = SignatureReplayDetector()
    findings = detector.detect(SAFE_SOURCE, "SafeSigVerifier.sol")
    assert len(findings) == 0
