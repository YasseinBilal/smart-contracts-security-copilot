"""Seed the vulnerability_embeddings table with known exploit knowledge.

Run: python -m app.memory.seed_knowledge
"""

import asyncio
import uuid

from app.database import AsyncSessionLocal
from app.memory.embedder import embed_batch
from app.models.embedding import VulnerabilityEmbedding

KNOWLEDGE_BASE = [
    # ---- REENTRANCY ----
    {
        "category": "REENTRANCY",
        "source": "rekt",
        "content": (
            "The DAO Hack (2016, $60M): Attacker exploited a reentrancy vulnerability in the "
            "splitDAO() function. The contract sent ETH to the attacker before updating the "
            "internal balance, allowing recursive calls that drained the contract repeatedly. "
            "Fix: Always update state BEFORE making external calls (CEI pattern). Use "
            "ReentrancyGuard.nonReentrant modifier as an additional safeguard."
        ),
    },
    {
        "category": "REENTRANCY",
        "source": "swc",
        "content": (
            "SWC-107 Reentrancy: A function makes an external call to another untrusted contract "
            "before resolving its effects on state. An attacker can use a fallback or receive() "
            "function to re-enter the calling function, repeatedly withdrawing funds. "
            "Detection: Look for .call{value:}(), .transfer(), .send() calls that appear BEFORE "
            "state variable assignments in the same function. "
            "Fix: Follow Checks-Effects-Interactions: check conditions, update state, then interact."
        ),
    },
    {
        "category": "REENTRANCY",
        "source": "swc",
        "content": (
            "Cross-function reentrancy: A contract calls an external contract which then calls "
            "a DIFFERENT function in the original contract that reads stale state. "
            "Example: withdraw() calls attacker, attacker calls transfer() which reads the "
            "not-yet-updated balance. Fix: Use a reentrancy lock (mutex) across all state-changing "
            "functions, not just the one making the external call."
        ),
    },
    # ---- ACCESS CONTROL ----
    {
        "category": "ACCESS_CONTROL",
        "source": "rekt",
        "content": (
            "Parity Multisig Freeze (2017, $150M): The Parity multisig wallet library contract "
            "had an initWallet() function that was public and not protected. An attacker called "
            "it to become the owner of the library, then called kill() to selfdestruct it, "
            "bricking all wallets that delegatecalled into it. "
            "Fix: Initialize proxy contracts in the constructor, never in a separate public "
            "initializer. Use OpenZeppelin's initializer modifier to prevent double-initialization."
        ),
    },
    {
        "category": "ACCESS_CONTROL",
        "source": "swc",
        "content": (
            "SWC-105 Unprotected Ether Withdrawal: A function that withdraws Ether lacks "
            "proper access control. Any address can call it and drain the contract. "
            "Detection: withdraw(), withdrawAll(), emergencyWithdraw() functions that are "
            "public/external without onlyOwner, onlyRole, or require(msg.sender == owner). "
            "Fix: Add appropriate access control. Consider using OpenZeppelin's Ownable or "
            "AccessControl contracts."
        ),
    },
    {
        "category": "ACCESS_CONTROL",
        "source": "swc",
        "content": (
            "SWC-106 Unprotected SELFDESTRUCT: A selfdestruct() call without access control "
            "allows any attacker to destroy the contract and send its balance to an arbitrary "
            "address. Detection: selfdestruct() or suicide() without an onlyOwner or role check. "
            "Fix: Gate selfdestruct behind strict access control and consider a time-lock."
        ),
    },
    # ---- ORACLE MANIPULATION ----
    {
        "category": "ORACLE_MANIPULATION",
        "source": "rekt",
        "content": (
            "bZx Flash Loan Attack (2020, $1M): Attacker took a flash loan, manipulated the "
            "price of WBTC on Uniswap by trading heavily, then used the manipulated price as "
            "oracle input to borrow more than collateral was worth. The protocol used spot price "
            "from an AMM as its oracle. "
            "Fix: Use time-weighted average prices (TWAP) over multiple blocks. Spot price from "
            "an AMM can be moved to any value within a single transaction using a flash loan."
        ),
    },
    {
        "category": "ORACLE_MANIPULATION",
        "source": "rekt",
        "content": (
            "Cream Finance ($130M, 2021): Attacker exploited Cream's price oracle that used "
            "Uniswap V2 spot price. By taking a flash loan and dumping tokens into the pair, "
            "the attacker collapsed the price, allowed undercollateralized borrowing, and drained "
            "the protocol. Fix: Chainlink decentralized oracle, or Uniswap V3 TWAP with "
            "sufficient window (30 minutes minimum for high-value protocols)."
        ),
    },
    {
        "category": "ORACLE_MANIPULATION",
        "source": "swc",
        "content": (
            "Spot price oracle risk: getReserves() from UniswapV2Pair returns the current reserves "
            "which can be manipulated by anyone within a transaction. Price = reserve0/reserve1 "
            "can be moved to near-infinity or near-zero using a flash loan. Any protocol that "
            "reads this value in the same transaction as a flash loan is vulnerable. "
            "Detection: getReserves() call without blockTimestampLast or TWAP computation nearby."
        ),
    },
    # ---- FLASH LOAN ----
    {
        "category": "FLASH_LOAN",
        "source": "rekt",
        "content": (
            "Euler Finance ($197M, 2023): Attacker found a missing health check in the "
            "donateToReserves() function that allowed creating bad debt via a flash loan. "
            "The attack exploited the interaction between flash loan, liquidation, and donation "
            "in a single transaction without needing the reserves to be solvent. "
            "Fix: Ensure health checks run after EVERY state change, even in flash loan callbacks."
        ),
    },
    {
        "category": "FLASH_LOAN",
        "source": "swc",
        "content": (
            "Flash loan callback verification: IERC3156 flash loan callbacks (onFlashLoan) "
            "must verify msg.sender is the trusted flash loan provider. Without this check, "
            "any contract can call the callback directly with crafted parameters, simulating "
            "a completed flash loan and triggering the post-loan logic without any actual loan. "
            "Detection: onFlashLoan or executeOperation functions without msg.sender check."
        ),
    },
    # ---- SIGNATURE REPLAY ----
    {
        "category": "SIGNATURE_REPLAY",
        "source": "rekt",
        "content": (
            "Poly Network ($611M, 2021): Attacker replayed a cross-chain transaction signature "
            "that lacked proper chain ID binding. The bridge contract verified ecrecover but "
            "did not include the destination chain ID in the signed message, allowing a valid "
            "signature from one chain to be replayed on another. "
            "Fix: Always include block.chainid in the signed message hash. Use EIP-712 with "
            "domain separator that includes chainId, verifyingContract."
        ),
    },
    {
        "category": "SIGNATURE_REPLAY",
        "source": "swc",
        "content": (
            "SWC-121 Missing Protection against Signature Replay Attacks: "
            "ecrecover() is used to verify a signature but the signed message does not include "
            "a nonce or a chain ID. This allows: (1) Same-chain replay: the same signature can "
            "be submitted multiple times. (2) Cross-chain replay: a signature valid on chain A "
            "is also valid on chain B with the same contract address. "
            "Fix: Include a per-user nonce in the signed data and consume it atomically. "
            "Include block.chainid in the domain separator (EIP-712 handles this)."
        ),
    },
    # ---- INTEGER OVERFLOW ----
    {
        "category": "INTEGER_OVERFLOW",
        "source": "rekt",
        "content": (
            "BECToken Overflow (2018): The batchTransfer() function multiplied _value by the "
            "number of recipients without overflow protection in Solidity ^0.4. The result "
            "wrapped to a small number, allowing the sender to drain massive amounts. "
            "Fix: Use SafeMath for all arithmetic in Solidity <0.8. In Solidity 0.8+, "
            "arithmetic reverts on overflow by default. Avoid unchecked{} blocks unless "
            "the overflow is intentional and provably safe."
        ),
    },
    {
        "category": "INTEGER_OVERFLOW",
        "source": "swc",
        "content": (
            "SWC-101 Integer Overflow and Underflow: In Solidity <0.8, integer arithmetic "
            "wraps silently. uint256 max + 1 = 0; uint256(0) - 1 = 2^256 - 1. "
            "This is especially dangerous in token balance accounting, loop conditions, "
            "and timestamp arithmetic. Detection: arithmetic operations without SafeMath in "
            "contracts with pragma solidity <0.8. Fix: Import and use SafeMath, or upgrade "
            "the Solidity version to 0.8+."
        ),
    },
    # ---- DELEGATECALL ----
    {
        "category": "DELEGATECALL",
        "source": "rekt",
        "content": (
            "Parity Multisig delegatecall (2017): The multisig wallet used delegatecall to "
            "a shared library contract. The library's initialize function was callable by anyone. "
            "An attacker called initWallet() on the library directly (not via delegatecall), "
            "became the owner, then called kill() to selfdestruct the library. All wallets that "
            "delegatecalled into it became permanently broken. "
            "Fix: Library contracts should not have state-changing initializers callable directly. "
            "Use the constructor for initialization. Verify storage layout compatibility."
        ),
    },
    {
        "category": "DELEGATECALL",
        "source": "swc",
        "content": (
            "SWC-112 Delegatecall to Untrusted Callee: delegatecall executes code from the "
            "target contract in the calling contract's storage context. If the storage layout "
            "of the caller and callee differ (different variable order/types), reads/writes "
            "will corrupt unintended storage slots. If the callee address is user-controlled, "
            "an attacker can point it to a malicious contract. "
            "Detection: delegatecall to a variable address (not a hardcoded constant). "
            "Fix: Ensure caller and callee have identical storage layout. Never delegatecall "
            "to user-supplied addresses."
        ),
    },
    # ---- UNCHECKED CALLS ----
    {
        "category": "UNCHECKED_CALLS",
        "source": "swc",
        "content": (
            "SWC-104 Unchecked Call Return Value: The return value of a message call "
            "(send, call, delegatecall) is not checked. If the call fails, execution "
            "continues as if it succeeded. This can lead to lost funds or inconsistent state. "
            "Detection: .send() without require(success), or .call() where the (bool, bytes) "
            "return is not captured. Fix: Always check: (bool success, ) = addr.call{value:v}(''); "
            "require(success, 'Transfer failed');"
        ),
    },
]


async def seed() -> None:
    texts = [entry["content"] for entry in KNOWLEDGE_BASE]
    print(f"Embedding {len(texts)} knowledge base entries...")

    from app.memory.embedder import embed_batch
    embeddings = await embed_batch(texts)

    async with AsyncSessionLocal() as db:
        for entry, embedding in zip(KNOWLEDGE_BASE, embeddings):
            record = VulnerabilityEmbedding(
                id=str(uuid.uuid4()),
                content=entry["content"],
                embedding=embedding,
                source=entry["source"],
                category=entry["category"],
                metadata_={},
            )
            db.add(record)
        await db.commit()

    print(f"Seeded {len(KNOWLEDGE_BASE)} vulnerability knowledge entries.")


if __name__ == "__main__":
    asyncio.run(seed())
