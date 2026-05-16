# Smart Contract Security AI Copilot

## What This Project Is
A portfolio-quality smart contract security analysis tool built to demonstrate:
1. Deep EVM vulnerability knowledge (not surface-level)
2. Production Python product engineering (FastAPI, SQLAlchemy, Alembic)
3. AI pipeline sophistication (LangGraph, multi-pass analysis, RAG)
4. Claude Code workflow mastery (hooks, subagents, MCP)

Apply to: product@sherlock.xyz (Web3 Product Engineer role)

---

## Domain Context: EVM Vulnerability Classes

### REENTRANCY
CEI (Checks-Effects-Interactions) violation — state change happens AFTER external call.
Attacker contract re-enters before balance/state is updated.
Real example: The DAO hack ($60M, 2016) — recursive call to splitDAO() drained funds.
Detection signal: `.call{value:}(`, `.transfer(`, `.send(` before a storage write in same function.
Fix: `nonReentrant` modifier (OpenZeppelin ReentrancyGuard), or restructure to CEI.

### ACCESS_CONTROL
Privileged functions callable by unauthorized actors. Missing modifiers, unguarded initializers.
Real example: Parity Multisig ($150M frozen, 2017) — `initWallet()` left callable by anyone on library contract.
Detection signal: `public` or `external` state-changing function with no `onlyOwner`/role modifier.

### INTEGER_OVERFLOW
Pre-Solidity 0.8 arithmetic wraps silently. `uint256(0) - 1 = 2^256 - 1`.
Real example: BECToken overflow (2018) — `batchTransfer()` multiplication overflow.
Fix: Use SafeMath (pre-0.8) or upgrade to Solidity ^0.8 (default overflow checks).
Note: `unchecked {}` blocks in 0.8+ re-enable overflow — always flag.

### ORACLE_MANIPULATION
Using spot price from AMM as truth within same transaction as a flash loan.
`getReserves()` from Uniswap V2 returns current reserves — manipulable intra-block.
Real examples: bZx ($1M, 2020), Cream Finance ($130M, 2021), Euler Finance ($197M, 2023).
Fix: TWAP (time-weighted average price) over multiple blocks. Chainlink oracle as secondary check.
Detection signal: `getReserves()` call without any `blockTimestampLast` or TWAP calculation nearby.

### FLASH_LOAN_ATTACK
Uncollateralized same-transaction loans used to manipulate collateral value, drain pools, or exploit governance.
Real example: Poly Network ($611M, 2021) — cross-chain message replay via flash loan.
Fix: Check balances before and after in same transaction, TWAP for pricing, flash loan guards.

### SIGNATURE_REPLAY
`ecrecover()` without nonce tracking allows reuse of signed messages.
Missing `chainId` allows cross-chain replay. Missing per-address nonce allows same-chain replay.
Real example: Poly Network ($611M, 2021) — no chainId in signed messages.
Detection signal: `ecrecover` call site with no mapping(address => uint256) nonce check.

### FRONT_RUNNING
Bots observe pending transactions in mempool and insert higher-gas transactions first.
Affects: DEX trades (sandwich attacks), liquidations, NFT mints, governance votes.
Fix: Commit-reveal schemes, slippage protection, deadline parameters.

### DELEGATECALL
`delegatecall` executes foreign code in current contract's storage context.
Storage layout mismatch between caller and callee leads to corruption.
Real example: Parity Multisig (again — library was `delegatecall`ed, storage slots misaligned).
Detection signal: `delegatecall` to user-supplied or upgradeable address.

---

## Sherlock Severity Framework (use this for all findings)
- CRITICAL: Direct, immediate fund loss. No preconditions required.
- HIGH: Significant fund loss under realistic conditions.
- MEDIUM: Limited impact OR requires specific conditions unlikely in practice.
- LOW: Best practices violation, code quality issue.
- INFO: Informational. No security impact.

---

## Architecture: Multi-Pass Analysis Pipeline

```
Solidity Source
    |
    v
[detectors/]  Static AST pattern matching (pure Python, fast, deterministic)
    |  StaticFinding[]
    v
[memory/]     pgvector RAG lookup — top-5 similar known exploits per finding
    |  rag_context[]
    v
[agents/]     LangGraph 7-node workflow — GPT-4o enriches + generates tests
    |  AIFinding[], test stubs, explanation
    v
[models/]     PostgreSQL persistence via SQLAlchemy
```

### LangGraph Nodes (in order)
1. `parse` — run Slither subprocess, parse JSON AST
2. `static_scan` — run DETECTORS registry against AST
3. `memory_query` — vector search for similar exploits per finding
4. `ai_reason` — GPT-4o: enrich findings, calibrate severity, remove false positives
5. `test_gen` — GPT-4o: Foundry test stub for each CRITICAL/HIGH finding
6. `explain` — GPT-4o: plain-English contract summary
7. `report` — assemble AuditReport, persist to DB

---

## Commands

```bash
# Start everything (first time: builds images + applies migrations)
docker compose up

# Run backend tests
docker compose exec backend pytest

# Run specific detector tests
docker compose exec backend pytest tests/test_detectors/

# Lint Python
ruff check backend/app/ && ruff format backend/app/

# Alembic migration
docker compose exec backend alembic revision --autogenerate -m "description"
docker compose exec backend alembic upgrade head

# Frontend dev (without Docker)
cd frontend && pnpm install && pnpm dev

# Seed vulnerability knowledge base
docker compose exec backend python -m app.memory.seed_knowledge
```

---

## Environment Variables

```
OPENAI_API_KEY=          # gpt-4o model calls AND text-embedding-3-small (same key)
DATABASE_URL=            # Set automatically by docker-compose
GITHUB_TOKEN=            # Optional: GitHub App integration
GITHUB_WEBHOOK_SECRET=   # Optional: webhook HMAC verification
```

---

## Adding a New Vulnerability Detector

1. Add category literal to `Severity` and `VulnCategory` in `backend/app/detectors/base.py`
2. Create `backend/app/detectors/{name}.py` implementing the `Detector` ABC
3. Register in `backend/app/detectors/registry.py` DETECTORS list
4. Add pytest file `backend/tests/test_detectors/test_{name}.py` with:
   - `VULNERABLE_SOURCE`: Solidity string that MUST trigger the detector
   - `SAFE_SOURCE`: Solidity string that MUST NOT trigger it
5. Update `backend/app/ai/prompts/system.py` with domain knowledge for this vuln class

---

## Claude Code Workflow Rules

### Hooks Active (do not disable)
- `PostToolUse(Write)` on `.py` files: runs `ruff format` + `ruff check --fix` automatically
- `PreToolUse(Bash)`: blocks `rm -rf` and `git push --force`
- `Stop`: appends session diff to `.claude/session-summaries.log`

### Subagents Available
- `vulnerability-scanner`: parallel analysis of multiple .sol files
- `cold-reviewer`: fresh-eye code review with no implementation context (reduces anchoring)
- `eval-agent`: benchmarks pipeline against example contracts

### Code Patterns to Follow
- All DB queries use `async with db.session() as session:` — never sync SQLAlchemy
- All OpenAI calls use `response_format={"type": "json_object"}` — never parse freeform text
- LangGraph nodes must be `async def` — sync nodes block the event loop
- Pydantic schemas validate ALL API inputs — never pass raw dicts to DB models
- Slither runner: always set timeout=60s — large contracts can hang

### Things Claude Gets Wrong on This Codebase
- Do NOT use `session.add()` then `await session.commit()` without `await session.flush()` first when you need the generated ID immediately
- Do NOT use `model="gpt-4"` — always use `model="gpt-4o"` (the correct current model)
- Do NOT import from `langchain` — this project uses `langgraph` directly
- Do NOT use `BaseModel` for LangGraph state — use `TypedDict` (LangGraph requirement)

---

## Key References
- SWC Registry (vulnerability classifications): https://swcregistry.io
- Rekt.news (real exploit post-mortems): https://rekt.news
- Sherlock judging criteria: https://docs.sherlock.xyz/audits/judging/judging
- pgvector cosine distance operator: `<=>` (smaller = more similar)
- LangGraph StateGraph docs: state must be TypedDict, nodes return partial state updates
