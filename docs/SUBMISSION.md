# AgentWallet Protocol — Hackathon Submission

**Colosseum Agent Hackathon 2026**
**Project:** AgentWallet Protocol
**Team:** @Web3__Youth / @agentwallet_pro
**Live:** [agentwallet.fun](https://agentwallet.fun)
**API:** [Live API](https://api.agentwallet.fun/health)
**GitHub:** [github.com/YouthAIAgent/agentwallet](https://github.com/YouthAIAgent/agentwallet)
**SDK:** [pypi.org/project/aw-protocol-sdk](https://pypi.org/project/aw-protocol-sdk/)
**Program ID:** `CEQLGCWkpUjbsh5kZujTaCkFB59EKxmnhsqydDzpt6r6` ([Solana Explorer](https://explorer.solana.com/address/CEQLGCWkpUjbsh5kZujTaCkFB59EKxmnhsqydDzpt6r6?cluster=devnet))

---

## 🔥 Try It NOW — Live on Solana Devnet

> **The API is live. The dashboard is live. The SDK is on PyPI. You can test everything right now.**

### Quick Start (3 minutes)

**Option A: Use the Dashboard** → [agentwallet.fun](https://agentwallet.fun)
1. Click "Dashboard" → Register with email + password
2. Create an agent → A wallet is auto-provisioned with a Solana devnet address
3. Airdrop devnet SOL → `solana airdrop 2 <wallet_address> --url devnet`
4. Transfer SOL, create escrow, set spending policies — all from the UI

**Option B: Use curl (API)**

```bash
# Base URL
API="https://api.agentwallet.fun"

# 1. Register (get JWT token)
curl -s -X POST $API/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"you@test.com","password":"MyAgent123","org_name":"MyOrg"}' | jq .

# Save your token
TOKEN="eyJhbG..."  # paste from response

# 2. Create an AI agent (wallet auto-provisioned)
curl -s -X POST $API/v1/agents \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"trading-bot","capabilities":["trading","data"]}' | jq .

# 3. List your agents + wallets
curl -s $API/v1/agents -H "Authorization: Bearer $TOKEN" | jq .
curl -s $API/v1/wallets -H "Authorization: Bearer $TOKEN" | jq .

# 4. Check wallet balance (use wallet address from step 2)
curl -s $API/v1/wallets/<wallet-id>/balance \
  -H "Authorization: Bearer $TOKEN" | jq .

# 5. Airdrop devnet SOL to your wallet address
solana airdrop 2 <wallet_address> --url devnet

# 6. Transfer SOL (policy-enforced, fee-deducted, audit-logged)
curl -s -X POST $API/v1/transactions/transfer-sol \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from_wallet_id": "<wallet-uuid>",
    "to_address": "11111111111111111111111111111111",
    "amount_sol": 0.01,
    "memo": "test transfer"
  }' | jq .

# 7. Set spending policy (per-tx limit)
curl -s -X POST $API/v1/policies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "daily-limit",
    "rules": {"spending_limit_lamports": 100000000, "daily_limit_lamports": 500000000},
    "scope_type": "org"
  }' | jq .

# 8. Create escrow (trustless agent-to-agent)
curl -s -X POST $API/v1/escrow \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "funder_wallet_id": "<wallet-uuid>",
    "recipient_address": "RecipientSolanaAddress...",
    "amount_sol": 0.5,
    "expires_in_hours": 24
  }' | jq .

# 9. View analytics
curl -s $API/v1/analytics/overview \
  -H "Authorization: Bearer $TOKEN" | jq .

# 10. View audit log
curl -s $API/v1/compliance/audit-log \
  -H "Authorization: Bearer $TOKEN" | jq .
```

**Option C: Use Python SDK**

```bash
pip install aw-protocol-sdk==0.4.0
```

```python
import asyncio
from agentwallet import AgentWallet

async def main():
    async with AgentWallet(
        base_url="https://api.agentwallet.fun",
        api_key="aw_live_..."  # or use JWT token
    ) as aw:
        # Create agent (wallet auto-provisioned)
        agent = await aw.agents.create(
            name="trading-bot",
            capabilities=["trading"]
        )
        print(f"Agent: {agent.id}")

        # List wallets
        wallets = await aw.wallets.list(agent_id=agent.id)
        wallet = wallets.data[0]
        print(f"Wallet: {wallet.address}")

        # Transfer SOL (after airdropping devnet SOL)
        tx = await aw.transactions.transfer_sol(
            from_wallet=wallet.id,
            to_address="RecipientAddress...",
            amount_sol=0.01
        )
        print(f"TX: {tx.signature}")

        # Create escrow
        escrow = await aw.escrow.create(
            funder_wallet=wallet.id,
            recipient_address="WorkerAgent...",
            amount_sol=0.5,
            expires_in_hours=24
        )
        print(f"Escrow: {escrow.id}")

        # Release escrow when task is done
        await aw.escrow.release(escrow.id)

asyncio.run(main())
```

**Option D: MCP (AI Agents)**

Any MCP-compatible AI can use AgentWallet as native tools. 27 tools available:
- `create_agent_wallet`, `transfer_sol`, `create_escrow`, `release_escrow`
- `check_balance`, `list_transactions`, `set_spending_policy`
- And 20 more...

### What You Can Test Right Now

| Feature | Endpoint | Status |
|---|---|---|
| Register & Auth | `POST /v1/auth/register` | ✅ Live |
| Create AI Agent | `POST /v1/agents` | ✅ Live |
| Auto-Provision Wallet | (auto on agent create) | ✅ Live |
| Check Balance | `GET /v1/wallets/{id}/balance` | ✅ Live |
| Transfer SOL | `POST /v1/transactions/transfer-sol` | ✅ Live |
| Spending Policies | `POST /v1/policies` | ✅ Live |
| Escrow (Create/Release/Refund) | `POST /v1/escrow` | ✅ Live |
| Analytics Dashboard | `GET /v1/analytics/overview` | ✅ Live |
| Audit Log | `GET /v1/compliance/audit-log` | ✅ Live |
| Agent Marketplace | `GET /v1/marketplace/listings` | ✅ Live |
| x402 Payments | `POST /v1/x402/pay` | ✅ Live |
| ERC-8004 Identity | `POST /v1/erc8004/register` | ✅ Live |
| Webhooks | `POST /v1/webhooks` | ✅ Live |

### Live URLs

| Resource | URL |
|---|---|
| **Landing Page** | [agentwallet.fun](https://agentwallet.fun) |
| **Dashboard** | [agentwallet.fun/dashboard.html](https://agentwallet.fun/dashboard.html) |
| **Docs** | [agentwallet.fun/docs.html](https://agentwallet.fun/docs.html) |
| **Quest Campaign** | [agentwallet.fun/quest.html](https://agentwallet.fun/quest.html) |
| **API Health** | [API /health](https://api.agentwallet.fun/health) |
| **Solana Program** | [Explorer (Devnet)](https://explorer.solana.com/address/CEQLGCWkpUjbsh5kZujTaCkFB59EKxmnhsqydDzpt6r6?cluster=devnet) |
| **SDK (PyPI)** | [aw-protocol-sdk](https://pypi.org/project/aw-protocol-sdk/) |
| **GitHub** | [YouthAIAgent/agentwallet](https://github.com/YouthAIAgent/agentwallet) |

---

## Endorsed by Solana Leadership

| Who | What They Said | Link |
|---|---|---|
| **toly** (Co-Founder, Solana Labs) | "EVM minds cannot comprehend this" — on AgentWallet's PDA vault architecture | [View](https://x.com/toly/status/2021861588656136303) |
| **Mike MacCana** (Solana Core Contributor) | "Narrative should have been ✨Solana has an inbuilt key value store✨" — validating our PDA-first approach | [View](https://x.com/mikemaccana/status/2021974942246695275) |
| **toly** (Co-Founder, Solana Labs) | "🛳️🛳️🛳️" — quote-tweeting AgentWallet's PDA Spend Policies launch | [View](https://x.com/toly/status/2022014589354094842) |

---

## Problem Statement

AI agents are becoming autonomous economic actors — they negotiate, trade, pay for services, and manage funds. But today, they operate with human wallets that were never designed for programmatic control.

**The result:**

- **No spending limits** — A compromised agent can drain everything
- **No escrow** — No trustless way for agents to pay each other for tasks
- **No audit trail** — Zero visibility into what agents are spending and why
- **No compliance** — No framework for EU AI Act, SOX, or regulatory reporting
- **Key management nightmare** — Private keys floating in `.env` files, one leak = game over

Every major AI lab (Anthropic, OpenAI, Google) is shipping agent frameworks. None of them have solved the wallet problem. Agents need financial infrastructure built for agents — not adapted human wallets.

---

## Technical Approach

### Architecture: 10-Layer Agentic Commerce Stack

AgentWallet is a **full-stack wallet-as-a-service protocol** built on Solana, designed ground-up for autonomous AI agents.

```
Foundation Model (LLM)
        ↕
MCP Layer (27 AI-native tools)
        ↕
Agent Identity & Registry
        ↕
AgentWallet Protocol (orchestration)
        ↕
x402 HTTP-Native Payments
        ↕
Universal Balance Aggregation
        ↕
Account Abstraction (PDAs)
        ↕
Stablecoin Settlement
        ↕
Wallet Engine (encrypted keys)
        ↕
Solana Blockchain (on-chain PDAs)
```

### On-Chain Program (Anchor/Rust)

Three PDAs power the core logic:

| PDA | Seeds | Purpose |
|---|---|---|
| `AgentWallet` | `["agent_wallet", org, agent_id]` | Per-tx + daily spending limits, spend tracking |
| `EscrowAccount` | `["escrow", escrow_id]` | Trustless fund locking with funder/recipient/arbiter |
| `PlatformConfig` | `["platform_config"]` | Fee wallet address, fee basis points |

**7 Anchor Instructions:**
- `create_agent_wallet` — Init wallet PDA with spending limits
- `transfer_with_limit` — Enforce limits → deduct fee → transfer SOL
- `update_limits` — Authority updates per-tx/daily limits
- `create_escrow` — Fund escrow PDA with SOL
- `release_escrow` — Release to recipient (funder/arbiter authorized)
- `refund_escrow` — Refund to funder (arbiter/expiry authorized)
- `initialize_platform_config` — Bootstrap fee configuration

**Security hardening (8 verified fixes):**
- Mandatory ENCRYPTION_KEY (no silent ephemeral key generation)
- Escrow PDA closing on release/refund (reclaim rent-exempt SOL)
- Zero-amount escrow validation
- Rate limiting on auth routes
- API key hashing upgraded to HMAC-SHA256
- JWT secret minimum 32-char validation
- Fee behavior fully documented
- Program ID placeholder warning for mainnet

### Backend (FastAPI + PostgreSQL + Redis)

- **13 API routers** covering agents, wallets, transactions, escrow, policies, analytics, compliance, webhooks, billing, auth, marketplace, erc8004, x402
- **16 SQLAlchemy models** — 14-table schema with full relational integrity
- **7 background workers** — tx processing, webhook delivery, analytics rollup, escrow expiry, usage metering
- **Permission Engine** — JSON policy rules evaluated on every transaction:
  - `spending_limit_lamports` (per-tx cap)
  - `daily_limit_lamports` (rolling 24h)
  - `destination_whitelist/blacklist`
  - `token_whitelist`
  - `time_window` restrictions
  - `require_approval_above` (human-in-the-loop for large amounts)
- **Dual auth** — JWT tokens + API keys (`aw_live_` / `aw_test_`)
- **Immutable audit log** for every state change
- **Anomaly detection** — velocity spikes, unusual amounts, high failure rates
- **Security headers** — HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy
- **Swagger disabled in production** — API docs only in development mode

### Python SDK (PyPI Published)

```bash
pip install aw-protocol-sdk==0.4.0
```

Stripe-like async client with typed responses:

```python
from agentwallet import AgentWallet

async with AgentWallet(api_key="aw_live_...") as aw:
    agent = await aw.agents.create(name="trading-bot", capabilities=["trading"])
    wallet = (await aw.wallets.list(agent_id=agent.id)).data[0]

    # Policy-enforced, fee-deducted, audit-logged transfer
    tx = await aw.transactions.transfer_sol(
        from_wallet=wallet.id,
        to_address="Recipient...",
        amount_sol=0.5
    )

    # Trustless escrow for agent-to-agent tasks
    escrow = await aw.escrow.create(
        funder_wallet=wallet.id,
        recipient_address="WorkerAgent...",
        amount_sol=1.0,
        expires_in_hours=24
    )
    await aw.escrow.release(escrow.id)
```

### MCP Integration (27 AI-Native Tools)

Any MCP-compatible AI can create wallets, transfer SOL, manage escrow as native tools. Zero integration friction — agents interact with AgentWallet the same way they interact with everything else.

### Dashboard (React + TypeScript)

9-page dark-themed hacker terminal dashboard: Dashboard overview, Agents, Wallets, Transactions, Analytics (Recharts), Policies, Audit Log, Billing, Login.

### Quest Campaign (Community Growth)

Supabase-backed anti-tamper quest system with:
- Magic link OTP authentication
- Server-side quest verification (no localStorage cheating)
- Daily check-in streaks with bonus multipliers
- Knowledge quiz (server-graded)
- Referral system with attribution
- Live leaderboard from real data
- Achievement badges (10 unlockable)
- XP/Level progression system (10 levels)

### CLI (Rich Terminal)

Live terminal dashboard with real-time stats, agent management, wallet operations.

---

## What Makes AgentWallet Different

| Feature | Human Wallets | AgentWallet |
|---|---|---|
| Spending Limits | ❌ None | ✅ Per-tx + daily caps |
| Escrow | ❌ Manual | ✅ On-chain PDA, trustless |
| Audit Trail | ❌ None | ✅ Immutable, every state change |
| Policy Engine | ❌ None | ✅ 7 rule types, auto-enforced |
| Agent Identity | ❌ Share human wallet | ✅ Dedicated PDA per agent |
| Key Security | ❌ `.env` files | ✅ Encrypted at rest (Fernet/KMS) |
| MCP Integration | ❌ None | ✅ 27 native tools |
| Compliance | ❌ None | ✅ EU AI Act reporting |
| Multi-agent | ❌ Not designed for it | ✅ Built for fleets of agents |

---

## Target Audience

### Primary
- **AI Agent Developers** building autonomous agents that need to transact (trading bots, data procurement agents, service agents)
- **AI Startups** deploying fleets of agents that manage funds (customer service, autonomous trading, content creation)
- **MCP Tool Builders** who want financial capabilities as plug-and-play tools

### Secondary
- **DeFi Protocols** integrating agent-based trading and liquidity management
- **Enterprise AI Teams** needing compliant, auditable agent financial operations
- **DAOs** using agents for treasury management with programmatic controls

### Market Size
The AI agent market is projected to reach $65B by 2030. Every one of these agents will need a wallet. AgentWallet is the infrastructure layer that makes that possible.

---

## Business Model

### Revenue Streams

1. **Transaction Fees** — Basis point fee on every on-chain transaction (configurable per platform deployment)
2. **Tiered API Access:**
   - **Free Tier** — 100 agents, 10K tx/month, community support
   - **Pro Tier** ($49/mo) — 1,000 agents, 100K tx/month, priority support, advanced analytics
   - **Enterprise** (Custom) — Unlimited, SLA, dedicated infrastructure, compliance reports
3. **Self-Hosted License** — Open-source core (MIT), premium enterprise features

### Unit Economics
- Near-zero marginal cost per transaction (Solana fees: ~$0.00025)
- Revenue scales linearly with agent economy growth
- Platform fees compound as agent-to-agent commerce increases

---

## Competitive Landscape

| Competitor | Approach | AgentWallet Advantage |
|---|---|---|
| **Coinbase CDP** | General wallet SDK, not agent-specific | Agent-native from day one: PDAs, policies, escrow |
| **Crossmint** | NFT/wallet API | No spending limits, no escrow, no compliance |
| **Dynamic.xyz** | Embedded wallets for users | Built for humans, not autonomous agents |
| **Turnkey** | Key management infra | Low-level — no policy engine, no analytics |
| **Circle (CCTP)** | Cross-chain USDC | Payment rail only — no agent identity or control |

**Our moat:** Purpose-built for the agentic economy. Not a human wallet adapted for agents — an agent wallet from the ground up.

---

## Future Vision

### Q1 2026 (Now)
- ✅ Core protocol live on Solana devnet
- ✅ Python SDK on PyPI (v0.2.0)
- ✅ 27 MCP tools
- ✅ Security audit complete (8 fixes shipped)
- ✅ Dashboard + CLI
- ✅ Agent-to-agent marketplace (v0.2.0)
- ✅ x402 HTTP-native payments (v0.2.0)
- ✅ ERC-8004 agent identity (v0.2.0)
- ✅ Agent reputation scoring (v0.2.0)
- ✅ Quest campaign with anti-tamper Supabase backend
- ✅ Security hardening (headers, CORS, password policy)

### Q2 2026
- Mainnet deployment on Solana
- TypeScript/Node.js SDK
- Cross-chain balance aggregation

### Q3 2026
- Multi-chain expansion (Base, Arbitrum, Polygon)
- Enterprise compliance suite (SOX, EU AI Act Article 52)

### Q4 2026
- Stablecoin settlement layer (USDC/USDT native)
- Account abstraction (gasless tx, session keys)
- AI-powered anomaly detection (ML models)
- 10,000+ agents target

### 2027
- Become the default wallet infrastructure for every AI agent framework
- Protocol-level interop with Anthropic, OpenAI, Google agent platforms
- On-chain agent reputation that serves as credit scoring
- Autonomous agent economy at scale

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Blockchain** | Solana, Anchor 0.30, Rust |
| **Backend** | FastAPI 0.115, SQLAlchemy 2.0, asyncpg, Alembic |
| **Database** | PostgreSQL 16 |
| **Cache/Queue** | Redis 7, arq |
| **Frontend** | React 18, TypeScript 5.6, Vite 6, Tailwind 3.4, Recharts |
| **Auth** | JWT (python-jose), bcrypt, API Keys |
| **Encryption** | Fernet (dev), AWS KMS (prod) |
| **SDK** | Python 3.11+, httpx, pydantic |
| **AI Integration** | MCP (Model Context Protocol), 27 tools |
| **Quest System** | Supabase (Auth + PostgreSQL + Realtime) |
| **Billing** | Stripe |
| **Logging** | structlog (JSON) |
| **Containers** | Docker Compose |
| **Testing** | pytest, pytest-asyncio, httpx (110/110 passing) |
| **CI/CD** | GitHub Actions |
| **Deploy** | Railway (API), Vercel (Landing), GitHub Pages |

---

## Codebase Stats

| Component | Count |
|---|---|
| MCP Tools | 47 |
| Anchor Instructions | 7 |
| API Routers | 13 |
| API Endpoints | 68 |
| SQLAlchemy Models | 15 |
| Database Tables | 14 |
| Background Workers | 7 |
| SDK Resources | 7 |
| Dashboard Pages | 9 |
| Test Files | 8 (53 tests passing) |
| Policy Rule Types | 7 |
| Security Fixes Shipped | 8 |
| Quest Types | 12 |
| Achievement Badges | 10 |

---

## Links

- **Live App:** [agentwallet.fun](https://agentwallet.fun)
- **Dashboard:** [agentwallet.fun/dashboard.html](https://agentwallet.fun/dashboard.html)
- **Docs:** [agentwallet.fun/docs.html](https://agentwallet.fun/docs.html)
- **Quest Campaign:** [agentwallet.fun/quest.html](https://agentwallet.fun/quest.html)
- **API Health:** [trustworthy-celebration-production-6a3e.up.railway.app/health](https://api.agentwallet.fun/health)
- **GitHub:** [github.com/YouthAIAgent/agentwallet](https://github.com/YouthAIAgent/agentwallet)
- **SDK (PyPI):** [pypi.org/project/aw-protocol-sdk](https://pypi.org/project/aw-protocol-sdk/)
- **Solana Program:** [Explorer (Devnet)](https://explorer.solana.com/address/CEQLGCWkpUjbsh5kZujTaCkFB59EKxmnhsqydDzpt6r6?cluster=devnet)
- **Twitter:** [@Web3__Youth](https://twitter.com/Web3__Youth) / [@agentwallet_pro](https://twitter.com/agentwallet_pro)
- **Hackathon Profile:** [colosseum.com/agent-hackathon/projects/agentwallet-protocol](https://colosseum.com/agent-hackathon/projects/agentwallet-protocol)

---

## Team

**Solo Builder** — @Web3__Youth

- 6 years in blockchain & crypto
- Built the entire stack: Anchor program, FastAPI backend, Python SDK, React dashboard, MCP server, CLI, Quest system
- Open source contributor, builder-first mentality
- Based in India, building for the global agentic economy

---

*"Your agents don't need permission. They need a wallet."*

**Vote for AgentWallet Protocol →** [colosseum.com/agent-hackathon/projects/agentwallet-protocol](https://colosseum.com/agent-hackathon/projects/agentwallet-protocol)
