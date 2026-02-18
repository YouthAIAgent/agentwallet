# AgentWallet Protocol — System Architecture

> **Version:** 1.0 · **Last Updated:** 2026-02-18  
> **Program ID:** `CEQLGCWkpUjbsh5kZujTaCkFB59EKxmnhsqydDzpt6r6`  
> **Status:** Live on Solana Devnet

---

## Overview

AgentWallet is a full-stack autonomous wallet infrastructure for AI agents on Solana. It combines:
- **On-chain security** via Anchor programs (PDA wallets with spending limits)
- **Off-chain API** via FastAPI (Python 3.11+)
- **Multi-platform SDKs** (Python + TypeScript)
- **MCP Server** with 33+ AI-native tools
- **React Dashboard** for human oversight

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CLIENTS & SDKs                                    │
│  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌──────────────┐ │
│  │ Dashboard │ │  Py SDK   │ │   TS SDK  │ │   CLI     │ │  MCP Clients │ │
│  │  React 18 │ │  PyPI     │ │   npm     │ │           │ │  (33 tools)  │ │
│  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └──────┬───────┘ │
└────────┼─────────────┼─────────────┼─────────────┼──────────────┼─────────┘
         │             │             │             │              │
         └─────────────┴─────────────┴─────────────┴──────────────┘
                                    │
                                    ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                     HTTPS / REST API Gateway                           │
  │                     JWT + API Key Auth                                 │
  │                     Rate Limiting (Redis)                              │
  └───────────────────────────────┬─────────────────────────────────────────┘
                                  │
                                  ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                       FastAPI Backend                                  │
  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ │
  │  │  Wallets  │ │  Escrow   │ │  Agents   │ │ Analytics │ │ Policies  │ │
  │  │  Router   │ │  Router   │ │  Router   │ │  Router   │ │  Router   │ │
  │  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ └─────┬─────┘ │
  │        │             │             │             │             │       │
  │  ┌─────┴─────────────┴─────────────┴─────────────┴─────────────┴─────┐ │
  │  │                    Core Services                                  │ │
  │  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐       │ │
  │  │  │   PDA     │ │   KMS     │ │  Config   │ │   Audit   │       │ │
  │  │  │ Module    │ │ (Fernet)  │ │  Engine   │ │  Logger   │       │ │
  │  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘       │ │
  │  └───────────────────────────────────────────────────────────────────┘ │
  └────────────────────────────────┬───────────────────────────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         │                         │                         │
         ▼                         ▼                         ▼
  ┌─────────────┐         ┌───────────────┐          ┌──────────────┐
  │   Solana    │         │  PostgreSQL   │          │   Redis 7    │
  │  Devnet/    │         │  + Alembic    │          │  (Cache +    │
  │  Mainnet    │         │               │          │  Rate Limit) │
  │  (Anchor)   │         │               │          │              │
  └─────────────┘         └───────────────┘          └──────────────┘
```

---

## Monorepo Structure

```
agentwallet/
├── packages/
│   ├── api/              # FastAPI backend (17 routers, 123 files)
│   │   ├── agentwallet/api/routers/    # 17 API routers
│   │   ├── agentwallet/core/           # PDA, KMS, config, database
│   │   ├── agentwallet/api/middleware/ # Auth, rate limit, audit
│   │   └── tests/                      # 110+ tests
│   ├── programs/         # Anchor/Rust smart contracts
│   │   └── agentwallet/
│   │       ├── src/lib.rs              # Program entry
│   │       ├── src/instructions/       # 6 anchor instructions
│   │       └── target/deploy/          # Deployed program
│   ├── dashboard/        # React 18 + Tailwind + Vite
│   ├── sdk-python/       # Python SDK (PyPI: aw-protocol-sdk)
│   ├── sdk-ts/           # TypeScript SDK
│   ├── mcp-server/       # MCP Server (33 tools)
│   └── cli/              # Command-line interface
├── docker-compose.yml    # Local dev stack
├── Dockerfile            # API container
└── Anchor.toml           # Solana program config
```

---

## On-Chain Architecture (Solana)

### Program: `CEQLGCWkpUjbsh5kZujTaCkFB59EKxmnhsqydDzpt6r6`

**Instructions:**
| Instruction | Purpose |
|-------------|---------|
| `create_agent_wallet` | Initialize PDA wallet with spending limits |
| `transfer_with_limit` | Execute SOL transfer with limit enforcement |
| `update_limits` | Modify spending policy (authority only) |
| `create_escrow` | Create funded escrow PDA |
| `release_escrow` | Release funds to recipient |
| `refund_escrow` | Return funds to funder (post-expiry) |

**PDA Accounts:**
| Account | Seeds | Purpose |
|---------|-------|---------|
| `AgentWallet` | `["agent_wallet", org, agent_id]` | Per-agent spending state |
| `EscrowAccount` | `["escrow", escrow_id]` | Locked funds with conditions |
| `PlatformConfig` | `["platform_config"]` | Fee settings (0.5%) |

---

## Security Model

| Layer | Implementation |
|-------|----------------|
| **Encryption** | Fernet (dev) / AWS KMS (prod) |
| **Auth** | JWT (24h expiry) + API Key (permanent) |
| **Rate Limiting** | Redis sliding window, tiered limits |
| **Audit** | All requests logged with metadata |
| **On-Chain** | PDA enforce limits, no API bypass |

---

## Deployment

| Environment | Platform | URL |
|-------------|----------|-----|
| Production | Railway | https://api.agentwallet.fun |
| Landing | Vercel | https://agentwallet.fun |
| Devnet | Solana | Program ID above |
| Docker | GHCR | ghcr.io/youthaiagent/agentwallet |

**Docker Compose Stack:**
- API container (FastAPI + Uvicorn)
- Worker container (Celery)
- PostgreSQL 16
- Redis 7

---

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic |
| Smart Contracts | Rust, Anchor 0.30, Borsh |
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| SDKs | Python (httpx), TypeScript (fetch) |
| Database | PostgreSQL 16, Redis 7 |
| Infrastructure | Docker, Railway, Vercel |
| CI/CD | GitHub Actions (pytest, ruff, CodeQL, Dependabot) |

---

## Data Flow

### Create PDA Wallet
```
Client → POST /v1/pda-wallets → API validates → Anchor tx → Solana
                                      ↓
                              PostgreSQL (metadata)
```

### Transfer with Limits
```
Client → POST /v1/pda-wallets/{id}/transfer
              → API validates limits → Anchor instruction
              → Solana enforces on-chain → Return signature
```

### Escrow Flow
```
Funder → create_escrow (funds locked)
              ↓
Worker → deliver work → funder releases → release_escrow
              ↓
         (or expiry) → refund_escrow
```

---

*See SECURITY_AUDIT.md for detailed security analysis.*
