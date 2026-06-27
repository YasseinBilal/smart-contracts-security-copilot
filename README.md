# SentinelAI — Smart Contract Security Copilot

AI-powered smart contract vulnerability detection with multi-pass analysis, Certora CVL property generation, persistent vulnerability memory, and an animated analysis dashboard.

## Quickstart

```bash
cp .env.example .env
# Add your OPENAI_API_KEY to .env

docker compose up
```

Open [http://localhost:3000](http://localhost:3000). Paste a GitHub contract URL or raw Solidity source and get researcher-level security findings.

## Architecture

```
                        Solidity Source
                              │
                              ▼
                    [FastAPI] POST /api/analyze
                              │  (SSE stream — live node-by-node updates)
                              ▼
              ┌───── LangGraph 8-Node Workflow ──────┐
              │  1. parse         → Slither AST       │
              │  2. static_scan   → Pattern detectors │
              │  3. memory_query  → pgvector RAG      │
              │  4. ai_reason     → GPT-4o enrichment │
              │  5. test_gen      → Foundry test stubs│
              │  6. property_gen  → Certora CVL stubs │
              │  7. explain       → Plain-English      │
              │  8. report        → DB persistence    │
              └───────────────────────────────────────┘
                              │
                              ▼
              [PostgreSQL 16 + pgvector]  ←── Vulnerability Knowledge Base
                              │                 (SWC Registry + Rekt.news)
                              ▼
              [React Dashboard]  — findings · CVL properties · Foundry tests
```

## Features

| Feature | Description |
| --- | --- |
| **GitHub URL Ingestion** | Paste a GitHub blob URL — source is auto-fetched and analysed |
| **Multi-Pass Analysis** | Static AST patterns → RAG lookup → GPT-4o reasoning → report |
| **8 Vulnerability Detectors** | Reentrancy, Access Control, Integer Overflow, Unchecked Calls, Oracle Manipulation, Signature Replay, Flash Loan, Delegatecall |
| **Vulnerability Memory** | pgvector knowledge base seeded with SWC Registry + Rekt.news post-mortems |
| **Foundry Test Stubs** | Exploit-reproducing Foundry tests for every CRITICAL/HIGH finding |
| **Certora CVL Properties** | Formal verification property stubs (invariants + rules) for each finding |
| **Animated Pipeline Progress** | Overlay panel with per-step status badges updating live via SSE |
| **Code Explanations** | Plain-English contract summary: what it does, who can call what, trust model |
| **GitHub PR Integration** | Webhook → automated PR review comments with severity-formatted findings |

## Vulnerability Coverage

| Class | Detector | Real-World Reference |
| --- | --- | --- |
| Reentrancy | CEI violation detection | The DAO ($60M, 2016) |
| Access Control | Unguarded privileged functions + camelCase set* setters | Parity Multisig ($150M, 2017) |
| Integer Overflow | Pre-0.8 arithmetic + unchecked blocks | BECToken (2018) |
| Unchecked Calls | `.send()` / `.call()` return ignored | SWC-104 |
| Oracle Manipulation | Spot price from AMM without TWAP | Cream Finance ($130M, 2021) |
| Signature Replay | Missing nonce + chainId in ecrecover | Poly Network ($611M, 2021) |
| Flash Loan | Callback without caller verification | Euler Finance ($197M, 2023) |
| Delegatecall | Mutable implementation address | Parity Library ($150M, 2017) |

## Stack

- **Backend**: Python 3.12 + FastAPI
- **AI Orchestration**: LangGraph (8-node stateful graph)
- **AI Model**: OpenAI GPT-4o with structured JSON output
- **Formal Verification**: Certora CVL property stubs (CALL hook, ghost variables, `@withrevert`)
- **Database**: PostgreSQL 16 + pgvector
- **ORM/Migrations**: SQLAlchemy 2 (asyncpg) + Alembic
- **Embeddings**: OpenAI `text-embedding-3-small`
- **Frontend**: React + TypeScript + Vite + TanStack Router
- **UI**: Tailwind CSS + Lucide icons
- **Local Infra**: Docker Compose (one command startup)

## Development

```bash
# Backend tests (detectors + LangGraph nodes)
docker compose exec backend uv run pytest tests/test_detectors/
docker compose exec backend uv run pytest tests/test_agents/

# Seed vulnerability knowledge base
docker compose exec backend python -m app.memory.seed_knowledge

# Frontend dev (hot reload, without Docker)
cd frontend && pnpm install && pnpm dev

# Add a new vulnerability detector
# 1. Create backend/app/detectors/{name}.py implementing Detector ABC
# 2. Register in backend/app/detectors/registry.py
# 3. Add test in backend/tests/test_detectors/test_{name}.py
# 4. Update CLAUDE.md with domain knowledge for GPT-4o prompts
```

## API Reference

| Endpoint | Method | Description |
| --- | --- | --- |
| `/api/analyze` | POST | Stream SSE analysis of a Solidity contract |
| `/api/scans` | GET | List all scans with severity counts |
| `/api/scans/{id}` | GET | Full scan detail with findings, CVL stubs, and test stubs |
| `/api/explain` | POST | Plain-English contract explanation |
| `/api/ingest` | POST | Clone GitHub repo and index .sol files |
| `/api/eval` | GET | Pipeline metrics (latency, token usage) |
| `/api/webhooks/github` | POST | GitHub App webhook for PR analysis |
| `/health` | GET | Health check |

## Environment Variables

```
OPENAI_API_KEY=sk-...          # Required: GPT-4o + text-embedding-3-small
```
