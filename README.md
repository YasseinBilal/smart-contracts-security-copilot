# SentinelAI — Smart Contract Security Copilot

AI-powered smart contract vulnerability detection with multi-pass analysis, persistent vulnerability memory, and an evaluation dashboard.

## Quickstart

```bash
cp .env.example .env
# Add your OPENAI_API_KEY to .env

docker compose up
```

Open [http://localhost:3000](http://localhost:3000). Paste any Solidity contract and get researcher-level security findings.

## Architecture

![Project Screenshot](https://i.ibb.co/XrMMdLtT/Screenshot-2026-05-16-at-13-06-40.png)

## Features

| Feature                       | Description                                                                                                                    |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **Repo Ingestion**            | Clone any GitHub repo, embed `.sol` files into pgvector for RAG                                                                |
| **Multi-Pass Analysis**       | Static AST patterns → RAG lookup → GPT-4o reasoning → report                                                                   |
| **8 Vulnerability Detectors** | Reentrancy, Access Control, Integer Overflow, Unchecked Calls, Oracle Manipulation, Signature Replay, Flash Loan, Delegatecall |
| **Vulnerability Memory**      | pgvector knowledge base seeded with SWC Registry + Rekt.news post-mortems                                                      |
| **Test Generation**           | Foundry test stubs for each CRITICAL/HIGH finding                                                                              |
| **Code Explanations**         | Plain-English contract summary: what it does, who can call what, trust model                                                   |
| **GitHub PR Integration**     | Webhook → automated PR review comments with severity-formatted findings                                                        |
| **Eval Dashboard**            | Latency per LangGraph node, false-positive rate, token usage per scan                                                          |

## Vulnerability Coverage

| Class               | Detector                              | Real-World Reference          |
| ------------------- | ------------------------------------- | ----------------------------- |
| Reentrancy          | CEI violation detection               | The DAO ($60M, 2016)          |
| Access Control      | Unguarded privileged functions        | Parity Multisig ($150M, 2017) |
| Integer Overflow    | Pre-0.8 arithmetic + unchecked blocks | BECToken (2018)               |
| Unchecked Calls     | `.send()` / `.call()` return ignored  | SWC-104                       |
| Oracle Manipulation | Spot price from AMM without TWAP      | Cream Finance ($130M, 2021)   |
| Signature Replay    | Missing nonce + chainId in ecrecover  | Poly Network ($611M, 2021)    |
| Flash Loan          | Callback without caller verification  | Euler Finance ($197M, 2023)   |
| Delegatecall        | Mutable implementation address        | Parity Library ($150M, 2017)  |

## Stack

- **Backend**: Python 3.12 + FastAPI
- **AI Orchestration**: LangGraph (7-node stateful graph)
- **AI Model**: OpenAI GPT-4o with structured JSON output
- **Database**: PostgreSQL 16 + pgvector
- **ORM/Migrations**: SQLAlchemy 2 (asyncpg) + Alembic
- **Embeddings**: OpenAI `text-embedding-3-small`
- **Frontend**: React + TypeScript + Vite + TanStack Router
- **UI**: Tailwind CSS + Recharts
- **Local Infra**: Docker Compose (one command startup)

## Development

```bash
# Backend tests (detectors + LangGraph nodes)
docker compose exec backend pytest tests/test_detectors/
docker compose exec backend pytest tests/test_agents/

# Seed vulnerability knowledge base
docker compose exec backend python -m app.memory.seed_knowledge

# Frontend dev (hot reload, without Docker)
cd frontend && pnpm install && pnpm dev

# Add a new vulnerability detector
# 1. Create backend/app/detectors/{name}.py implementing Detector ABC
# 2. Register in backend/app/detectors/registry.py
# 3. Add test in backend/tests/test_detectors/test_{name}.py
# 4. Update CLAUDE.md with domain knowledge
```

## API Reference

| Endpoint               | Method | Description                                      |
| ---------------------- | ------ | ------------------------------------------------ |
| `/api/analyze`         | POST   | Stream SSE analysis of a Solidity contract       |
| `/api/scans`           | GET    | List all scans with severity counts              |
| `/api/scans/{id}`      | GET    | Full scan detail with findings                   |
| `/api/explain`         | POST   | Plain-English contract explanation               |
| `/api/ingest`          | POST   | Clone GitHub repo and index .sol files           |
| `/api/eval`            | GET    | Pipeline metrics (latency, FP rate, token usage) |
| `/api/webhooks/github` | POST   | GitHub App webhook for PR analysis               |
| `/health`              | GET    | Health check                                     |

## Environment Variables

```
OPENAI_API_KEY=sk-...          # Required: GPT-4o + text-embedding-3-small
```
