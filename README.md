```
     █████╗  ██████╗ ███████╗███╗   ██╗████████╗    ██╗    ██╗ █████╗ ██╗     ██╗     ███████╗████████╗
    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝    ██║    ██║██╔══██╗██║     ██║     ██╔════╝╚══██╔══╝
    ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║       ██║ █╗ ██║███████║██║     ██║     █████╗     ██║
    ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║       ██║███╗██║██╔══██║██║     ██║     ██╔══╝     ██║
    ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║       ╚███╔███╔╝██║  ██║███████╗███████╗███████╗   ██║
    ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝        ╚══╝╚══╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚══════╝   ╚═╝
```

# AgentWallet Protocol

**Autonomous financial infrastructure for AI agents on Solana.**

[![Solana Devnet](https://img.shields.io/badge/Solana-Devnet%20Deployed-9945FF?style=for-the-badge&logo=solana)](https://explorer.solana.com/address/CEQLGCWkpUjbsh5kZujTaCkFB59EKxmnhsqydDzpt6r6?cluster=devnet)
[![PyPI Package](https://img.shields.io/pypi/v/aw-protocol-sdk?style=for-the-badge&logo=pypi&logoColor=white&label=PyPI)](https://pypi.org/project/aw-protocol-sdk/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Rust Anchor](https://img.shields.io/badge/Rust-Anchor%200.30-000000?style=for-the-badge&logo=rust)](https://anchor-lang.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)
[![Live Demo](https://img.shields.io/badge/Demo-agentwallet.fun-00ff41?style=for-the-badge&logo=vercel)](https://agentwallet.fun)
[![API Live](https://img.shields.io/badge/API-Live%20on%20Railway-0B0D0E?style=for-the-badge&logo=railway)](https://trustworthy-celebration-production-6a3e.up.railway.app/docs)

> _"Your agents don't need permission. They need a wallet."_

### Endorsed by Solana Leadership

<a href="https://x.com/toly/status/2021861588656136303">
  <img src="docs/images/endorsement-combined.png" alt="Endorsed by toly and Mike MacCana" width="800" />
</a>

> **"EVM minds cannot comprehend this"** — [toly](https://x.com/toly/status/2021861588656136303), Co-Founder of Solana Labs
>
> **"Narrative should have been: ✨Solana has an inbuilt key value store✨"** — [Mike MacCana](https://x.com/mikemaccana/status/2021974942246695275), Solana Core Contributor
>
> **"🛳️🛳️🛳️"** — [toly](https://x.com/toly/status/2022014589354094842), on AgentWallet's PDA Spend Policies launch

---

## Try It NOW — Live on Solana Devnet

**Program ID:** `CEQLGCWkpUjbsh5kZujTaCkFB59EKxmnhsqydDzpt6r6`

| Resource | URL |
|---|---|
| **Website** | [agentwallet.fun](https://agentwallet.fun) |
| **Dashboard** | [agentwallet.fun/dashboard.html](https://agentwallet.fun/dashboard.html) |
| **Docs** | [agentwallet.fun/docs.html](https://agentwallet.fun/docs.html) |
| **Quest Campaign** | [agentwallet.fun/quest.html](https://agentwallet.fun/quest.html) |
| **API** | [Live API](https://trustworthy-celebration-production-6a3e.up.railway.app/health) |
| **Solana Explorer** | [View on Devnet](https://explorer.solana.com/address/CEQLGCWkpUjbsh5kZujTaCkFB59EKxmnhsqydDzpt6r6?cluster=devnet) |
| **SDK** | `pip install aw-protocol-sdk==0.2.0` |

### Quick Test (Copy-Paste These Commands)

```bash
# Set base URL
API="https://trustworthy-celebration-production-6a3e.up.railway.app"

# 1. Register → get JWT token
curl -s -X POST $API/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"MyAgent123","org_name":"TestOrg"}'

# 2. Create AI agent (auto-provisions Solana devnet wallet)
curl -s -X POST $API/v1/agents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"trading-bot","capabilities":["trading"]}'

# 3. Airdrop devnet SOL to your agent's wallet
solana airdrop 2 WALLET_ADDRESS --url devnet

# 4. Transfer SOL (policy-enforced, fee-deducted, audit-logged)
curl -s -X POST $API/v1/transactions/transfer-sol \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"from_wallet_id":"WALLET_UUID","to_address":"11111111111111111111111111111111","amount_sol":0.01}'

# 5. Create escrow (trustless agent-to-agent payment)
curl -s -X POST $API/v1/escrow \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"funder_wallet_id":"WALLET_UUID","recipient_address":"RECIPIENT","amount_sol":0.5,"expires_in_hours":24}'

# 6. Set spending policy
curl -s -X POST $API/v1/policies \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"daily-cap","rules":{"daily_limit_lamports":500000000},"scope_type":"org"}'
```

**Full testing guide with SDK + MCP examples:** [docs/SUBMISSION.md](docs/SUBMISSION.md)

**Production-ready on Solana devnet.** Mainnet deployment scheduled for Q2 2026.

---

## Why AgentWallet?

- **🤖 Agent-Native:** Built specifically for autonomous AI agents, not human wallets
- **⚡ Programmable Limits:** Spending caps, time windows, whitelist/blacklist per agent
- **🔐 Trustless Escrow:** On-chain PDAs for agent-to-agent task payments
- **📊 Real-time Analytics:** Complete audit trail and compliance reporting

---

## The Problem

AI agents are becoming autonomous economic actors. They negotiate, trade, pay for services, and manage funds. But they're operating with human wallets, human limits, and zero programmatic control.

No spending limits. No escrow. No audit trail. No compliance. No agent-native wallet infra.

**That era is over.**

---

## What Is AgentWallet

AgentWallet is a **wallet-as-a-service protocol** built for autonomous AI agents on Solana. It gives every agent its own on-chain identity with programmable spending limits, trustless escrow, real-time analytics, and full compliance — all accessible through a single SDK call.

```
┌─────────────────────────────────────────────────────────────────┐
│                        AGENTWALLET                              │
│                                                                 │
│   SDK (Python)  ──►  REST API  ──►  Solana Program (Anchor)    │
│   Dashboard     ──►  Workers   ──►  PostgreSQL + Redis          │
│   CLI           ──►  Webhooks  ──►  On-chain PDAs               │
│                                                                 │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│   │  Wallet  │  │  Escrow  │  │  Policy  │  │ Analytics│      │
│   │  Engine  │  │  Engine  │  │  Engine  │  │  Engine  │      │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                                                                 │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│   │   Fee    │  │Compliance│  │  Billing │  │  Agent   │      │
│   │Collector │  │  Module  │  │ (Stripe) │  │ Registry │      │
│   └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Quick Install & Deploy

### Install SDK

```bash
pip install aw-protocol-sdk==0.2.0
```

### MCP Server (AI-Native Tools)

```bash
pip install agentwallet-mcp
```

Any MCP-compatible AI can now create wallets, transfer SOL, manage escrow — as native tools. **27 tools** covering the full protocol. [See MCP docs →](agentwallet/packages/mcp-server/README.md)

### Deploy Your First Agent

```python
from agentwallet import AgentWallet

async with AgentWallet(api_key="aw_live_...") as aw:

    # Spawn agent with its own wallet
    agent = await aw.agents.create(
        name="trading-bot-alpha",
        capabilities=["trading", "payments"]
    )

    # Agent's wallet is ready
    wallet = (await aw.wallets.list(agent_id=agent.id)).data[0]
    print(f"Agent wallet: {wallet.address}")

    # Send SOL (policy-enforced, fee-deducted, audit-logged)
    tx = await aw.transactions.transfer_sol(
        from_wallet=wallet.id,
        to_address="RecipientPubkey...",
        amount_sol=0.5,
    )
    print(f"TX: {tx.signature}")

    # Lock funds in escrow for a task
    escrow = await aw.escrow.create(
        funder_wallet=wallet.id,
        recipient_address="WorkerAgentPubkey...",
        amount_sol=1.0,
        expires_in_hours=24,
    )

    # Release on task completion
    await aw.escrow.release(escrow.id)
```

---

## Self-Hosted Deployment

### 1. Clone & Boot

```bash
git clone git@github.com:YouthAIAgent/agentwallet.git
cd agentwallet/agentwallet

cp .env.example .env
# Edit .env with your ENCRYPTION_KEY and SOLANA_RPC_URL

docker compose up -d
```

```
 ✔ postgres   healthy
 ✔ redis      healthy
 ✔ api        running   → http://localhost:8000
 ✔ worker     running
 ✔ dashboard  running   → http://localhost:5173
```

### 2. Run Migrations

```bash
docker compose exec api alembic upgrade head
```

### 3. Register & Get Your Key

```bash
curl -X POST http://localhost:8000/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"org_name": "my-org", "email": "admin@my-org.ai", "password": "supersecret"}'
```

```json
{
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "access_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

**You're live.** Your agents now have wallets.

---

## Roadmap

- ✅ **Core Protocol** — Wallets, escrow, policies, analytics
- ✅ **Python SDK** — Published on PyPI (`pip install aw-protocol-sdk`)
- ✅ **Devnet Deployment** — Live on Solana devnet with program ID
- ✅ **Security Audit & Hardening** — Production-ready security model
- ✅ **MCP Integration** — 27 AI-native tools via Model Context Protocol
- ✅ **A2A Commerce Protocol** — Agent-to-agent marketplace (v0.2.0)
- ✅ **x402 Payments** — HTTP-native auto-pay middleware (v0.2.0)
- ✅ **ERC-8004 Identity** — On-chain agent identity system (v0.2.0)
- ✅ **Agent Reputation System** — On-chain reputation scoring (v0.2.0)
- 📋 **Multi-chain Support** — EVM L2s (Arbitrum, Base, Polygon)
- 📋 **Mainnet Launch** — Production deployment (Q2 2026)

---

## Architecture

```
                    ┌──────────────┐
                    │   Clients    │
                    │ SDK/Dash/CLI │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   nginx      │
                    │  rate limit  │
                    │     SSL      │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   FastAPI    │  ← 13 routers, 3 middleware layers
                    │   /v1/*      │  ← JWT + API Key dual auth
                    └──┬───────┬───┘
                       │       │
              ┌────────▼─┐  ┌──▼────────┐
              │PostgreSQL │  │   Redis   │
              │   16      │  │    7      │
              │  (ACID)   │  │ (cache +  │
              │           │  │  queues)  │
              └────────┬──┘  └──┬────────┘
                       │       │
                    ┌──▼───────▼──┐
                    │   Workers   │
                    │             │
                    │ tx_proc  5s │
                    │ webhooks 1s │
                    │ analytics60s│
                    │ escrow  300s│
                    │ usage  3600s│
                    └──────┬──────┘
                           │
                    ┌──────▼───────┐
                    │  Solana RPC  │
                    │              │
                    │ AgentWallet  │  ← Anchor program
                    │   Program    │  ← On-chain PDAs
                    └──────────────┘
```

---

## Monorepo Structure

```
agentwallet/
│
├── docker-compose.yml          # Full stack: PG + Redis + API + Worker + Dashboard
├── Dockerfile                  # API container
├── Dockerfile.worker           # Background worker container
├── pyproject.toml              # Root Python config
├── alembic.ini                 # Migration config
├── .env.example                # All env vars documented
│
└── packages/
    │
    ├── api/                    # ── BACKEND ──────────────────────
    │   └── agentwallet/
    │       ├── main.py         # FastAPI entrypoint
    │       ├── core/           # Config, DB, Redis, Solana, KMS, Retry
    │       ├── models/         # 15+ SQLAlchemy ORM models
    │       ├── services/       # 13+ business logic services
    │       ├── api/
    │       │   ├── routers/    # 13 route modules
    │       │   ├── schemas/    # 13+ Pydantic schema modules
    │       │   └── middleware/ # Auth, Rate Limit, Audit
    │       ├── workers/        # 5 background workers + scheduler
    │       └── migrations/     # Alembic (001_initial = 14 tables)
    │
    ├── sdk-python/             # ── PYTHON SDK ───────────────────
    │   └── src/agentwallet/
    │       ├── client.py       # Stripe-like async client
    │       ├── types.py        # Typed dataclass responses
    │       ├── exceptions.py   # Error hierarchy
    │       └── resources/      # agents, wallets, transactions,
    │                           # escrow, analytics, policies
    │
    ├── dashboard/              # ── WEB DASHBOARD ────────────────
    │   └── src/
    │       ├── App.tsx         # React Router + Auth Guard
    │       ├── api.ts          # Typed API client
    │       ├── components/     # Sidebar (lucide-react icons)
    │       └── pages/          # 9 pages: Dashboard, Agents,
    │                           # Wallets, Transactions, Analytics,
    │                           # Policies, AuditLog, Billing, Login
    │
    ├── programs/               # ── SOLANA PROGRAM ───────────────
    │   └── agentwallet/
    │       └── src/
    │           ├── lib.rs      # 7 instructions (Anchor)
    │           ├── state.rs    # PDAs: AgentWallet, Escrow, Config
    │           ├── errors.rs   # 10 custom error variants
    │           └── instructions/
    │               ├── create_agent_wallet.rs
    │               ├── transfer_with_limit.rs
    │               ├── update_limits.rs
    │               └── escrow.rs
    │
    ├── landing/                # ── MARKETING SITE ───────────────
    │   └── src/                # Landing page and docs
    │
    └── cli/                    # ── OPERATOR CLI ─────────────────
        └── agentwallet_cli/
            ├── main.py         # 6 commands (argparse + httpx)
            └── dashboard.py    # Rich live terminal dashboard
```

---

## Core Systems

### Wallet Engine
Every agent gets a dedicated Solana wallet. Private keys are encrypted at rest (Fernet dev / AWS KMS prod). Balances are Redis-cached. Keys **never** leave the server.

```
Agent Created → Keypair Generated → Key Encrypted (KMS) → Wallet Stored → Address Returned
                                                            ↓
                                              Private key NEVER in API response
```

### Permission Engine
JSON-based policy rules evaluated on every transaction before it hits the chain.

| Rule | Description |
|---|---|
| `spending_limit_lamports` | Max per-transaction amount |
| `daily_limit_lamports` | Rolling 24h spending cap |
| `destination_whitelist` | Only send to approved addresses |
| `destination_blacklist` | Block specific addresses |
| `token_whitelist` | Restrict to approved SPL tokens |
| `time_window` | Only allow transactions in specific hours |
| `require_approval_above` | Human approval for large amounts |

Three outcomes: **`ALLOW`** | **`DENY`** | **`REQUIRE_APPROVAL`**

### Transaction Engine
```
Idempotency Check
       ↓
Permission Engine (policies)
       ↓
Fee Calculation (tier-based BPS)
       ↓
Build TX (net amount + fee instruction)
       ↓
Sign (multi-signer support)
       ↓
Submit to Solana
       ↓
Confirm (polling with backoff)
       ↓
Audit Log + Webhooks
```

Supports: SOL transfers, SPL token transfers, batch transfers (semaphore-gated `asyncio.gather`), idempotency keys.

### Escrow Service
Trustless escrow for agent-to-agent task payments.

```
CREATED ──► FUNDED ──┬──► RELEASED  (funder/arbiter confirms delivery)
                     ├──► REFUNDED  (arbiter rules in funder's favor)
                     ├──► DISPUTED  (either party raises dispute)
                     └──► EXPIRED   (auto-refund after deadline)
```

On-chain PDA holds the funds. No one can rug.

### Analytics Engine
Pre-aggregated daily rollups. Org-level and per-agent breakdowns. Spending trends, cost forecasting, CSV export.

### Compliance Module
Immutable audit trail for every state change. Anomaly detection (velocity spikes, unusual amounts, high failure rates). EU AI Act Article 52 report generation.

---

## On-Chain Program (Anchor/Rust)

Three PDAs power the on-chain logic:

| PDA | Seeds | Purpose |
|---|---|---|
| `AgentWallet` | `["agent_wallet", org, agent_id]` | Per-tx + daily spending limits, daily spend counter |
| `EscrowAccount` | `["escrow", escrow_id]` | Lock funds with funder/recipient/arbiter/expiry |
| `PlatformConfig` | `["platform_config"]` | Fee wallet address, fee basis points |

**Instructions:**

| Instruction | What It Does |
|---|---|
| `create_agent_wallet` | Init wallet PDA with spending limits |
| `transfer_with_limit` | Enforce limits → deduct fee → transfer SOL |
| `update_limits` | Authority updates per-tx/daily limits |
| `create_escrow` | Fund escrow PDA with SOL |
| `release_escrow` | Release to recipient (funder/arbiter) |
| `refund_escrow` | Refund to funder (arbiter/expiry) |
| `initialize_platform_config` | Bootstrap fee configuration |

---

## API Reference

Base URL: `http://localhost:8000/v1`

### Auth
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create org + get JWT |
| `POST` | `/auth/login` | Login + get JWT |
| `POST` | `/auth/api-keys` | Generate API key |
| `GET` | `/auth/api-keys` | List API keys |
| `DELETE` | `/auth/api-keys/{id}` | Revoke API key |

### Agents
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/agents` | Register agent (auto-creates wallet) |
| `GET` | `/agents` | List agents |
| `GET` | `/agents/{id}` | Get agent details |
| `PATCH` | `/agents/{id}` | Update agent |

### Wallets
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/wallets` | Create wallet |
| `GET` | `/wallets` | List wallets |
| `GET` | `/wallets/{id}` | Get wallet |
| `GET` | `/wallets/{id}/balance` | Get SOL + SPL balances |

### Transactions
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/transactions/transfer-sol` | Send SOL (policy-enforced) |
| `POST` | `/transactions/batch-transfer` | Batch SOL transfers |
| `GET` | `/transactions` | List transactions |
| `GET` | `/transactions/{id}` | Get transaction |

### Escrow
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/escrow` | Create + fund escrow |
| `GET` | `/escrow` | List escrows |
| `GET` | `/escrow/{id}` | Get escrow |
| `POST` | `/escrow/{id}/action` | Release / Refund / Dispute |

### Policies
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/policies` | Create policy |
| `GET` | `/policies` | List policies |
| `PATCH` | `/policies/{id}` | Update policy |
| `DELETE` | `/policies/{id}` | Delete policy |

### Analytics
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/analytics/summary` | Org overview stats |
| `GET` | `/analytics/daily` | Daily metrics |
| `GET` | `/analytics/agents` | Per-agent breakdown |

### Compliance
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/compliance/audit-log` | Immutable audit trail |
| `GET` | `/compliance/anomalies` | Detected anomalies |
| `GET` | `/compliance/reports/{type}` | Compliance reports |

### Webhooks
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/webhooks` | Subscribe to events |
| `GET` | `/webhooks` | List webhooks |
| `PATCH` | `/webhooks/{id}` | Update webhook |
| `DELETE` | `/webhooks/{id}` | Delete webhook |

### Tokens
| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/tokens/balances/{wallet_id}` | Get token balances |
| `POST` | `/tokens/transfer` | Transfer SPL tokens |
| `GET` | `/tokens/metadata/{mint}` | Get token metadata |

### Marketplace
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/marketplace/services` | Register agent service |
| `GET` | `/marketplace/services` | Discover services |
| `POST` | `/marketplace/hire` | Hire an agent |
| `GET` | `/marketplace/stats` | Marketplace statistics |

### ERC-8004
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/erc8004/identity` | Register agent identity |
| `GET` | `/erc8004/identity/{agent_id}` | Get agent identity |

### x402
| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/x402/pay` | Process x402 payment |
| `GET` | `/x402/verify/{payment_id}` | Verify payment status |

---

## SDK Usage

```bash
pip install aw-protocol-sdk==0.2.0
```

```python
from agentwallet import AgentWallet

async with AgentWallet(api_key="aw_live_xxx") as aw:

    # ── Agents ──────────────────────────────────────
    agent = await aw.agents.create(
        name="sniper-bot",
        description="High-frequency trading agent",
        capabilities=["trading", "payments", "escrow"]
    )

    # ── Wallets ─────────────────────────────────────
    wallets = await aw.wallets.list(agent_id=agent.id)
    balance = await aw.wallets.get_balance(wallets.data[0].id)
    print(f"Balance: {balance.sol_balance} SOL")

    # ── Transactions ────────────────────────────────
    tx = await aw.transactions.transfer_sol(
        from_wallet=wallets.data[0].id,
        to_address="Recipient...",
        amount_sol=0.1,
        memo="Payment for data feed"
    )

    # ── Escrow ──────────────────────────────────────
    escrow = await aw.escrow.create(
        funder_wallet=wallets.data[0].id,
        recipient_address="WorkerAgent...",
        amount_sol=2.0,
        expires_in_hours=48,
        conditions={"task": "train-model-v2"}
    )
    await aw.escrow.release(escrow.id)

    # ── Policies ────────────────────────────────────
    await aw.policies.create(
        name="Daily Cap",
        rules={"daily_limit_lamports": 5_000_000_000},
        scope_type="agent",
        scope_id=agent.id,
    )

    # ── Analytics ───────────────────────────────────
    summary = await aw.analytics.summary()
    print(f"Total spend: {summary.total_spend_lamports} lamports")
```

---

## Dashboard

Dark-themed React dashboard at `http://localhost:5173`.

| Page | What You See |
|---|---|
| **Dashboard** | Stat cards, spend charts (Recharts), agent activity |
| **Agents** | CRUD table, status, reputation scores |
| **Wallets** | Addresses, balances, types, fund actions |
| **Transactions** | Filterable TX history with status badges |
| **Analytics** | Line charts, bar charts, spending breakdowns |
| **Policies** | Accordion view, JSON rule editor |
| **Audit Log** | Immutable event stream with filters |
| **Billing** | Tier comparison, usage meters, Stripe portal |

---

## CLI

```bash
# Status overview
python -m agentwallet_cli status

# Manage agents
python -m agentwallet_cli agents list
python -m agentwallet_cli agents create --name "my-agent"

# Manage wallets
python -m agentwallet_cli wallets list
python -m agentwallet_cli wallets balance <wallet-id>

# View transactions
python -m agentwallet_cli transactions list --limit 20

# Live terminal dashboard (Rich)
python -m agentwallet_cli dashboard
```

```
┌─ AgentWallet Dashboard ──────────────────────────────────────┐
│                                                              │
│  ┌─ Overview ───┐  ┌─ Agents ──────────────────────────────┐ │
│  │ Agents:  12  │  │ NAME            STATUS   REPUTATION   │ │
│  │ Wallets: 34  │  │ trading-bot     active   0.95         │ │
│  │ TX/24h:  847 │  │ data-agent      active   0.88         │ │
│  │ Volume: 142◎ │  │ payment-relay   paused   0.72         │ │
│  └──────────────┘  └──────────────────────────────────────┘ │
│                                                              │
│  ┌─ Recent Transactions ────────────────────────────────────┐ │
│  │ TIME     TYPE      AMOUNT    STATUS     SIGNATURE        │ │
│  │ 14:32    sol_tx    0.50 SOL  confirmed  4xK9...mP2      │ │
│  │ 14:31    escrow    2.00 SOL  funded     7bR3...nQ8      │ │
│  │ 14:28    sol_tx    0.10 SOL  confirmed  2cT5...vL4      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌─ Active Escrows ──────┐  ┌─ Policies ─────────────────┐  │
│  │ ID       STATUS  AMT  │  │ NAME           ENABLED PRI │  │
│  │ esc_01   funded  2◎   │  │ Daily Cap      yes     10  │  │
│  │ esc_02   funded  5◎   │  │ Whitelist      yes     20  │  │
│  └────────────────────────┘  └────────────────────────────┘  │
│                                                              │
│  Refreshing every 5s...                        [Q] Quit      │
└──────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

```
BACKEND         FastAPI 0.115 · SQLAlchemy 2.0 · asyncpg · Alembic
CACHE/QUEUE     Redis 7 · arq
DATABASE        PostgreSQL 16
BLOCKCHAIN      Solana · solders 0.27 · Anchor 0.30 (Rust)
FRONTEND        React 18 · TypeScript 5.6 · Vite 6 · Tailwind 3.4 · Recharts
AUTH            JWT (python-jose) · bcrypt (direct) · API Keys
ENCRYPTION      Fernet (dev) · AWS KMS (prod)
BILLING         Stripe
LOGGING         structlog (JSON)
CONTAINERS      Docker Compose
TESTING         pytest · pytest-asyncio · httpx
LINTING         ruff · mypy
```

---

## Development

```bash
# Install Python dependencies
pip install -e ".[dev]"

# Run API locally
uvicorn agentwallet.main:app --reload --port 8000

# Run workers
python -m agentwallet.workers.scheduler

# Run tests
pytest packages/api/tests/ -v

# Run dashboard
cd packages/dashboard && npm install && npm run dev

# Build Solana program
cd packages/programs/agentwallet && anchor build

# Lint
ruff check packages/api/
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|:---:|---|---|
| `DATABASE_URL` | Yes | -- | PostgreSQL connection string |
| `REDIS_URL` | Yes | -- | Redis connection string |
| `SOLANA_RPC_URL` | Yes | devnet | Solana RPC endpoint |
| `ENCRYPTION_KEY` | Yes | -- | Fernet key for wallet encryption |
| `JWT_SECRET_KEY` | Yes | -- | JWT signing secret |
| `PLATFORM_WALLET_ADDRESS` | Yes | -- | Receives platform fees |
| `STRIPE_SECRET_KEY` | No | -- | Stripe billing |
| `AWS_KMS_KEY_ID` | No | -- | Production key encryption |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `LOG_FORMAT` | No | `json` | `json` or `text` |

Generate encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Database Schema

14 tables. Partitioned by month at scale.

```
organizations ─┬─► users
               ├─► api_keys
               ├─► agents ──────► wallets
               ├─► transactions
               ├─► escrows
               ├─► policies
               ├─► approval_requests
               ├─► audit_events
               ├─► analytics_daily
               ├─► webhooks ────► webhook_deliveries
               └─► usage_meters
```

---

## Security

- Private keys encrypted at rest (Fernet / AWS KMS)
- Private keys **never** exposed via API
- JWT + API Key dual authentication
- bcrypt password hashing
- Redis-backed rate limiting per tier
- Immutable audit log for all state changes
- HMAC-signed webhook deliveries
- CORS + input validation on all endpoints
- Idempotency keys prevent double-spend

---

## Contributing

We welcome contributions! Please see our [contributing guidelines](CONTRIBUTING.md) for details.

### Getting Started

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Ensure tests pass: `pytest packages/api/tests/`
5. Lint your code: `ruff check packages/api/`
6. Commit your changes: `git commit -m 'Add amazing feature'`
7. Push to the branch: `git push origin feature/amazing-feature`
8. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/agentwallet.git
cd agentwallet

# Install dependencies
pip install -e ".[dev]"

# Start development environment
docker compose up -d postgres redis
uvicorn agentwallet.main:app --reload
```

### Code Style

- Python: `ruff` for linting and formatting
- TypeScript: `eslint` + `prettier` for frontend
- Rust: `rustfmt` for Solana programs
- Commit messages: [Conventional Commits](https://conventionalcommits.org/)

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Built by

**[@Web3__Youth](https://twitter.com/Web3__Youth)** — Building the financial infrastructure for the agentic economy.

AgentWallet is part of our mission to enable autonomous AI agents to participate meaningfully in digital economies. We're building the tools that let agents be economic actors, not just assistants.

---

## Get Involved

⭐ **Star this repository** if you believe in agent-native financial infrastructure

🐦 **Follow us on Twitter:** [@Web3__Youth](https://twitter.com/Web3__Youth)

💬 **Join our community:** [Discord](https://discord.gg/agentwallet) (coming soon)

🔗 **Connect:** [LinkedIn](https://linkedin.com/company/youthaiagent)

---

<p align="center">
  <strong>Built for the agentic economy.</strong><br>
  <sub>Every agent deserves a wallet. Every wallet deserves limits. Every transaction deserves a trail.</sub>
</p>

<p align="center">
  <a href="https://github.com/YouthAIAgent/agentwallet">🌟 Star on GitHub</a> •
  <a href="https://pypi.org/project/aw-protocol-sdk/">📦 SDK on PyPI</a> •
  <a href="https://explorer.solana.com/address/CEQLGCWkpUjbsh5kZujTaCkFB59EKxmnhsqydDzpt6r6?cluster=devnet">⛓️ Live on Solana</a> •
  <a href="https://twitter.com/Web3__Youth">🐦 Follow Us</a>
</p>