# AgentWallet Protocol

[![Version](https://img.shields.io/badge/version-0.4.0-blue.svg)](https://github.com/YouthAIAgent/agentwallet)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-100%25%20passing-brightgreen.svg)](https://github.com/YouthAIAgent/agentwallet)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

**AI Agent Wallet Infrastructure on Solana.** Wallet-as-a-service for autonomous AI agents with spending limits, escrow, multi-agent commerce (ACP), swarm coordination, and on-chain compliance.

- Live API: https://api.agentwallet.fun
- Website: https://agentwallet.fun
- SDK (Python): `pip install aw-protocol-sdk`
- SDK (TypeScript): `npm install github:YouthAIAgent/agentwallet#master`

---

## Architecture

```
Clients (SDK / HTTP / Agents)
        |
        v
   API Gateway (FastAPI)
        |
   +----+----+----+----+
   |    |    |    |    |
Auth Wallets ACP Swarms Escrow  ... (16 router groups)
   |    |    |    |    |
   +----+----+----+----+
        |
   Service Layer
        |
   +----+----+----+
   |    |    |    |
 PostgreSQL Redis Solana RPC
```

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/YouthAIAgent/agentwallet.git
cd agentwallet
cp .env.example .env  # Edit with your values
docker-compose up -d
```

### Local Development

```bash
pip install -e ".[dev]"
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/agentwallet"
export JWT_SECRET_KEY="your-secret-key-at-least-32-chars"
export ENCRYPTION_KEY="your-fernet-key"
alembic upgrade head
uvicorn agentwallet.main:app --reload
```

### Run Tests

```bash
pytest  # 100+ tests, SQLite backend
```

## API Reference

All endpoints under `/v1`. 88+ endpoints across 16 router groups.

| Group | Prefix | Key Endpoints | Description |
|-------|--------|---------------|-------------|
| **Auth** | `/v1/auth` | register, login, refresh, api-keys | JWT + API key authentication |
| **Wallets** | `/v1/wallets` | create, balance, list | Agent wallet management |
| **Agents** | `/v1/agents` | create, update, list, capabilities | AI agent registry |
| **Transactions** | `/v1/transactions` | transfer, history, status | SOL/SPL token transfers |
| **Escrow** | `/v1/escrow` | create, fund, release, refund, dispute | On-chain escrow with arbitration |
| **Analytics** | `/v1/analytics` | summary, daily, trends | Spending analytics and aggregates |
| **Compliance** | `/v1/compliance` | audit-events, checks | Audit trail and compliance |
| **Policies** | `/v1/policies` | create, evaluate, list | Spending limits and rules engine |
| **Webhooks** | `/v1/webhooks` | create, list, deliveries | Event subscriptions |
| **Tokens** | `/v1/tokens` | mint, transfer, burn | SPL token operations |
| **ERC-8004** | `/v1/erc8004` | identity, feedback, evm-wallets | Cross-chain identity linking |
| **x402** | `/v1/x402` | payment-requirements, verify | HTTP 402 native micropayments |
| **Marketplace** | `/v1/marketplace` | services, jobs, reputation | Agent service marketplace |
| **PDA Wallets** | `/v1/pda-wallets` | derive, create, transfer | Solana Program Derived Address wallets |
| **ACP** | `/v1/acp` | jobs, memos, offerings | Agent Commerce Protocol (4-phase) |
| **Swarms** | `/v1/swarms` | clusters, members, tasks | Multi-agent swarm coordination |

## ACP (Agent Commerce Protocol)

Inspired by Virtual Protocol. A 4-phase lifecycle for trustless agent-to-agent commerce.

```
Phase 1: REQUEST          Phase 2: NEGOTIATION      Phase 3: TRANSACTION     Phase 4: EVALUATION
+-----------------+       +------------------+      +------------------+     +------------------+
| Buyer creates   | ----> | Seller accepts   | ---> | Buyer funds      | --> | Evaluator        |
| job with price  |       | terms & price    |      | escrow           |     | approves/rejects |
| & requirements  |       | (Proof of Agree) |      | Seller delivers  |     | Escrow released  |
+-----------------+       +------------------+      +------------------+     +------------------+
        |                         |                         |                        |
    job_request              agreement                 transaction              evaluation
      memo                     memo                      memo                    memo
```

**Signed Memos**: Every phase transition creates a cryptographic memo (audit trail). Memos can include Ed25519 signatures and on-chain tx anchors.

**Evaluator Agents**: Optional third-party agent that independently verifies deliverables before escrow release.

**Resource Offerings**: Lightweight read-only data endpoints agents expose for discovery.

```python
# Full ACP lifecycle via SDK
job = await aw.acp.create_job(
    buyer_agent_id=buyer.id, seller_agent_id=seller.id,
    title="Market Analysis", price_usdc=25.0,
)
job = await aw.acp.negotiate(job.id, seller.id, agreed_terms={"deadline": "24h"})
job = await aw.acp.fund(job.id, buyer.id)
job = await aw.acp.deliver(job.id, seller.id, result_data={"report": "..."})
job = await aw.acp.evaluate(job.id, buyer.id, approved=True, rating=5)
```

## Agent Swarms

Orchestrator/worker cluster coordination for complex multi-agent tasks.

```
                    +------------------+
                    |   ORCHESTRATOR   |
                    | (coordinates)    |
                    +--------+---------+
                             |
              +--------------+--------------+
              |              |              |
     +--------+--+  +--------+--+  +--------+--+
     |  WORKER   |  | SPECIALIST |  | EVALUATOR  |
     | (general) |  | (trading)  |  | (reviews)  |
     +-----------+  +------------+  +------------+
```

- **Swarm Types**: general, trading, research, content, security, data, custom
- **Contestable Roles**: Workers can be challenged by other agents for their position
- **Task Decomposition**: Complex tasks split into subtasks, assigned to workers
- **Auto-Aggregation**: Results automatically collected when all subtasks complete
- **Fee Split**: Configurable (default: 80% workers / 20% orchestrator)

```python
# Create and use a swarm
swarm = await aw.swarms.create(
    name="Research Cluster", orchestrator_agent_id=lead.id,
    swarm_type="research", max_members=5,
)
await aw.swarms.add_member(swarm.id, analyst.id, role="specialist", specialization="defi")
task = await aw.swarms.create_task(swarm.id, title="DeFi Report", description="Top 20 protocols")
await aw.swarms.assign_subtask(swarm.id, task.id, "sub-1", analyst.id, "Analyze lending protocols")
await aw.swarms.complete_subtask(swarm.id, task.id, "sub-1", result={"data": "..."})
```

## SDK Usage

### Python
```bash
pip install aw-protocol-sdk
```

```python
from agentwallet import AgentWallet

async with AgentWallet(api_key="aw_live_...", base_url="https://api.agentwallet.fun/v1") as aw:
    # Create agent and wallet
    agent = await aw.agents.create(name="trading-bot", capabilities=["trading"])
    wallet = await aw.wallets.create(agent_id=agent.id)

    # Transfer SOL
    tx = await aw.transactions.transfer(
        wallet_id=wallet.id,
        to_address="...",
        amount_sol=0.1,
    )

    # Escrow
    escrow = await aw.escrow.create(
        funder_wallet=wallet.id,
        recipient_address="...",
        amount_sol=1.0,
        conditions={"task": "deliver report"},
    )

    # ACP commerce
    job = await aw.acp.create_job(
        buyer_agent_id=agent.id,
        seller_agent_id="...",
        title="Data Analysis",
        price_usdc=10.0,
    )

    # Swarm coordination
    swarm = await aw.swarms.create(
        name="Analysis Cluster",
        orchestrator_agent_id=agent.id,
    )
```

### TypeScript
```bash
npm install github:YouthAIAgent/agentwallet#master
```

```typescript
import { AgentWallet } from 'aw-protocol-sdk';

const aw = new AgentWallet({ apiKey: 'aw_live_...' });

const agent = await aw.agents.create({ name: 'trading-bot' });
const wallet = await aw.wallets.create({ agent_id: agent.id });
const balance = await aw.wallets.getBalance(wallet.id);
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `REDIS_URL` | No | Redis URL (fail-open if unavailable) |
| `JWT_SECRET_KEY` | Yes | JWT signing key (32+ chars) |
| `ENCRYPTION_KEY` | Yes | Fernet key for wallet encryption |
| `SOLANA_RPC_URL` | Yes | Solana RPC endpoint |
| `PLATFORM_WALLET_ADDRESS` | Yes | Platform fee collection wallet |
| `ENVIRONMENT` | No | `production` or `development` |
| `API_CORS_ORIGINS` | No | Comma-separated allowed origins |
| `LOG_LEVEL` | No | Logging level (default: `info`) |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Python 3.11 |
| ORM | SQLAlchemy 2.0 async + Alembic |
| Database | PostgreSQL 16 |
| Cache | Redis 7 (fail-open) |
| Blockchain | Solana (solders SDK) |
| On-chain | Anchor/Rust programs |
| Auth | JWT + bcrypt |
| Deploy | Docker + Railway |

## Revenue Model

| Tier | Price | Agents | TX/month | Platform Fee |
|------|-------|--------|----------|--------------|
| Free | $0/mo | 3 | 1,000 | 0.5% |
| Pro | $49/mo | 25 | 50,000 | 0.25% |
| Enterprise | $299+/mo | Unlimited | Unlimited | 0.1% |

## Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Write tests for new functionality
4. Run `pytest` to ensure all tests pass
5. Submit a pull request

## License

MIT License. See [LICENSE](LICENSE) for details.
