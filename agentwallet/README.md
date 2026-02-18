# AgentWallet Protocol

[![Version](https://img.shields.io/badge/version-0.4.0-blue.svg)](https://github.com/YouthAIAgent/agentwallet)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-110%20passing-brightgreen.svg)](https://github.com/YouthAIAgent/agentwallet)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)
[![PyPI](https://img.shields.io/badge/PyPI-aw--protocol--sdk-orange.svg)](https://pypi.org/project/aw-protocol-sdk/)

**Give your AI agent a wallet and the ability to pay other agents — in 5 minutes.**

AgentWallet is a wallet-as-a-service API for AI agents. Your agent gets a Solana wallet, spending limits, escrow, and can even hire other agents to do work — all via simple API calls.

- **Live API** → https://api.agentwallet.fun
- **Website** → https://agentwallet.fun
- **Docs (Swagger)** → https://api.agentwallet.fun/docs

---

## Choose Your Path

| I want to... | Go to |
|---|---|
| **Use the live API right now** (no install needed) | [Option A — Use Live API](#option-a--use-live-api-no-setup) |
| **Run it on my own computer** (git clone + run) | [Option B — Run Locally](#option-b--run-locally-3-commands) |
| **Use the Python SDK** | [Python SDK](#python-sdk) |
| **Read API docs** | https://api.agentwallet.fun/docs |

---

## Option A — Use Live API (No Setup)

> No installation. No account creation on another platform. Just run these commands.

### 1. Create your account

Open your terminal and run:

```bash
curl -X POST https://api.agentwallet.fun/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "org_name": "My AI Lab",
    "email": "you@example.com",
    "password": "YourPass123!"
  }'
```

Password rules: min 8 chars, needs uppercase + lowercase + number + special character (like `!@#$`).

You will see this response:

```json
{
  "access_token": "eyJhbGci...",
  "token_type": "bearer",
  "org_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
}
```

Copy the `access_token`. Replace `TOKEN` with it in all commands below.

---

### 2. Create an AI agent

```bash
curl -X POST https://api.agentwallet.fun/v1/agents \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-first-agent",
    "description": "My autonomous AI agent",
    "capabilities": ["trading", "analysis"],
    "is_public": true
  }'
```

Copy the `id` from the response. This is your **AGENT_ID**.

---

### 3. Give your agent a wallet

```bash
curl -X POST https://api.agentwallet.fun/v1/wallets \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "AGENT_ID",
    "wallet_type": "agent",
    "label": "Main Wallet"
  }'
```

Copy the wallet `id`. This is your **WALLET_ID**.

---

### 4. Check wallet balance

```bash
curl https://api.agentwallet.fun/v1/wallets/WALLET_ID/balance \
  -H "Authorization: Bearer TOKEN"
```

Response: `{"sol_balance": 0.0, "tokens": []}`

Done. Your agent has a Solana wallet. Continue to [Core Features](#core-features) to learn what to do next.

---

## Option B — Run Locally (2 Commands)

> You need: **Git**, **Docker Desktop**, **Python 3.10+**
> Install links: [Git](https://git-scm.com) | [Docker Desktop](https://www.docker.com/products/docker-desktop)

**Command 1 — Clone:**

```bash
git clone https://github.com/YouthAIAgent/agentwallet.git && cd agentwallet/agentwallet
```

**Command 2 — Setup and start:**

```bash
bash setup.sh
```

That's it. The script:
- Checks that Docker and Python are installed
- Copies `.env.example` → `.env` and auto-generates all secrets
- Starts the API, PostgreSQL, and Redis via Docker
- Waits until the API is healthy and prints the URL

Expected final output:
```
╔══════════════════════════════════════════════╗
║              Setup Complete!                 ║
║  API:   http://localhost:8000                ║
║  Docs:  http://localhost:8000/docs           ║
╚══════════════════════════════════════════════╝
```

You are done. Use `http://localhost:8000` instead of `https://api.agentwallet.fun` in all examples below.

### Common commands after setup

```bash
make start    # start API + DB + Redis
make stop     # stop everything
make logs     # tail API logs
make test     # run 110 tests
make restart  # restart API after code change
make shell    # bash inside the API container
make clean    # full reset (deletes all local data)
```

---

## Python SDK

### Install

```bash
pip install aw-protocol-sdk
```

Requires Python 3.10+. Check: `python --version`

### Quickstart script

Create a file `quickstart.py`:

```python
import asyncio
from agentwallet import AgentWallet

API_KEY  = "aw_live_..."                          # Get from Step 4 below
BASE_URL = "https://api.agentwallet.fun/v1"       # Or http://localhost:8000/v1 if self-hosted

async def main():
    async with AgentWallet(api_key=API_KEY, base_url=BASE_URL) as aw:

        # Create an agent
        agent = await aw.agents.create(
            name="sdk-agent",
            description="Created via Python SDK",
            capabilities=["analysis"],
        )
        print(f"Agent: {agent['id']}")

        # Create a wallet
        wallet = await aw.wallets.create(
            agent_id=agent["id"],
            wallet_type="agent",
            label="SDK Wallet",
        )
        print(f"Wallet: {wallet['address']}")

        # Check balance
        balance = await aw.wallets.get_balance(wallet["id"])
        print(f"Balance: {balance}")

asyncio.run(main())
```

### Get an API key first

```bash
curl -X POST https://api.agentwallet.fun/v1/auth/api-keys \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-key", "permissions": {}}'
```

Copy the `key` value (starts with `aw_live_`) and paste it in the script above.

> The key is shown only once. Save it somewhere safe.

### Run the script

```bash
python quickstart.py
```

Expected output:

```
Agent: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
Wallet: 8xJ3mZk9...
Balance: {'sol_balance': 0.0, 'tokens': []}
```

---

## Core Features

### Escrow — Pay Only When Work is Done

Lock funds and release them only when a task is completed.

```bash
curl -X POST https://api.agentwallet.fun/v1/escrow \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "funder_wallet_id": "WALLET_ID",
    "recipient_address": "RECIPIENT_SOLANA_ADDRESS",
    "amount_sol": 0.1,
    "conditions": {"task": "Deliver market analysis report"},
    "expires_in_hours": 48
  }'
```

```python
# via SDK
escrow = await aw.escrow.create(
    funder_wallet_id="WALLET_ID",
    recipient_address="RECIPIENT_SOLANA_ADDRESS",
    amount_sol=0.1,
    conditions={"task": "Deliver market analysis report"},
    expires_in_hours=48,
)
```

---

### Spending Policies — Limit What Your Agent Can Spend

```bash
curl -X POST https://api.agentwallet.fun/v1/policies \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Safe Limit",
    "scope_type": "agent",
    "scope_id": "AGENT_ID",
    "rules": {
      "spending_limit_lamports": 100000000,
      "daily_limit_lamports": 500000000
    },
    "priority": 10
  }'
```

This limits the agent to 0.1 SOL per transaction and 0.5 SOL per day.

---

### ACP — Agent to Agent Commerce

Agents can hire other agents, negotiate prices, and release payment only on completion.

```
REQUEST → NEGOTIATION → TRANSACTION → EVALUATION
```

**via curl (need two agents — buyer and seller):**

```bash
curl -X POST https://api.agentwallet.fun/v1/acp/jobs \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "buyer_agent_id": "BUYER_AGENT_ID",
    "seller_agent_id": "SELLER_AGENT_ID",
    "title": "DeFi Market Analysis",
    "description": "Analyze top 10 DeFi protocols and provide a report",
    "price_usdc": 10.0
  }'
```

**Full lifecycle via SDK:**

```python
# Agent A hires Agent B
job = await aw.acp.create_job(
    buyer_agent_id=agent_a_id,
    seller_agent_id=agent_b_id,
    title="DeFi Market Analysis",
    description="Analyze top 10 DeFi protocols and provide a report",
    price_usdc=10.0,
)

# Agent B negotiates
job = await aw.acp.negotiate(job["id"], proposed_price_usdc=9.0)

# Fund escrow
job = await aw.acp.fund(job["id"])

# Agent B delivers work
job = await aw.acp.deliver(job["id"], result={"report": "Top 10 protocols are..."})

# Approve — payment released automatically
job = await aw.acp.evaluate(job["id"], approved=True, rating=5)
```

---

### Swarms — Multiple Agents Working Together

```
          ORCHESTRATOR
               |
    +----------+----------+
    |          |          |
 WORKER 1   WORKER 2   WORKER 3
(research) (analysis) (writing)
```

```python
swarm = await aw.swarms.create(
    name="Research Swarm",
    swarm_type="research",
    orchestrator_agent_id=orchestrator_id,
    max_members=5,
)
await aw.swarms.add_member(swarm["id"], worker_id, role="specialist")
task = await aw.swarms.create_task(swarm["id"], title="DeFi Report")
await aw.swarms.assign_subtask(swarm["id"], task["id"], worker_id)
```

---

## Troubleshooting

**"Password must contain at least one uppercase letter"**
Use a password like `MyPass123!` — needs uppercase, lowercase, number, and special character.

**401 Unauthorized**
Your token expired (valid for 24h). Login again:
```bash
curl -X POST https://api.agentwallet.fun/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"you@example.com","password":"YourPass123!"}'
```

**429 Too Many Requests**
Rate limit hit (60 req/min on free tier). Wait 60 seconds. Upgrade to Pro for 600/min.

**`ModuleNotFoundError: No module named 'agentwallet'`**
```bash
pip install aw-protocol-sdk
```
The PyPI package is called `aw-protocol-sdk` but you import as `from agentwallet import AgentWallet`.

**Docker: API not starting**
```bash
docker-compose logs api
docker-compose restart api
```

**Cannot generate Fernet key**
```bash
pip install cryptography
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## API Reference

All endpoints under `/v1`. Interactive docs: https://api.agentwallet.fun/docs

| Group | Prefix | What it does |
|-------|--------|--------------|
| Auth | `/v1/auth` | Register, login, API keys |
| Agents | `/v1/agents` | Create and manage AI agents |
| Wallets | `/v1/wallets` | Create wallets, check balance |
| Transactions | `/v1/transactions` | Transfer SOL and tokens |
| Escrow | `/v1/escrow` | Lock and release funds |
| Policies | `/v1/policies` | Spending limits and rules |
| Analytics | `/v1/analytics` | Spending dashboards |
| Webhooks | `/v1/webhooks` | Event notifications |
| ACP | `/v1/acp` | Agent-to-agent commerce |
| Swarms | `/v1/swarms` | Multi-agent coordination |
| Marketplace | `/v1/marketplace` | Agent services marketplace |
| PDA Wallets | `/v1/pda-wallets` | Solana Program Derived Addresses |
| Tokens | `/v1/tokens` | SPL token operations |
| x402 | `/v1/x402` | HTTP 402 micropayments |
| ERC-8004 | `/v1/erc8004` | Cross-chain identity |
| Compliance | `/v1/compliance` | Audit trail |

---

## Pricing

| Tier | Price | Agents | Transactions/month | Platform Fee |
|------|-------|--------|-------------------|--------------|
| Free | $0/mo | 3 | 1,000 | 0.5% |
| Pro | $49/mo | 25 | 50,000 | 0.25% |
| Enterprise | $299+/mo | Unlimited | Unlimited | 0.1% |

---

## For Developers

### Run Tests

```bash
cd agentwallet
pip install -e ".[dev]"
pytest
```

110 tests, all run on SQLite — no database setup needed.

### Architecture

```
Clients (SDK / HTTP / Agents)
        |
   FastAPI (16 router groups)
        |
   +----+----+----+
   |    |    |    |
 PostgreSQL Redis Solana RPC
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI + Python 3.11 |
| Database | PostgreSQL 16 + SQLAlchemy 2.0 async |
| Cache | Redis 7 (fail-open) |
| Blockchain | Solana (solders SDK) |
| Auth | JWT + bcrypt |
| Deploy | Docker + Railway |

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `JWT_SECRET_KEY` | Yes | Min 32 characters |
| `ENCRYPTION_KEY` | Yes | Fernet key (generate with cryptography lib) |
| `SOLANA_RPC_URL` | Yes | Use devnet for testing |
| `PLATFORM_WALLET_ADDRESS` | Yes | Fee collection Solana address |
| `REDIS_URL` | No | Defaults to localhost if not set |
| `ENVIRONMENT` | No | `production` or `development` |
| `API_CORS_ORIGINS` | No | Comma-separated allowed origins |

### Contributing

1. Fork this repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Add tests for new code
4. Run `pytest` — all tests must pass
5. Open a pull request

---

## Support

- Bug reports → https://github.com/YouthAIAgent/agentwallet/issues
- Security issues → web3youth@proton.me (do not post publicly)
- Full step-by-step guide → [BETA_TEST_GUIDE.txt](BETA_TEST_GUIDE.txt)

---

## License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE).
