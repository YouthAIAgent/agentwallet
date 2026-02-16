# Community Posts & Awesome List Submissions

## PART 1: REDDIT POSTS

---

### r/solana

**Title:** `I built open-source wallet infrastructure for AI agents on Solana — PDA-enforced spending limits, trustless escrow, agent marketplace`

**Body:**

Hey r/solana,

I've been working on something at the intersection of AI agents and Solana — **AgentWallet**, an open-source wallet-as-a-service for autonomous AI agents.

**The problem:** AI agents are getting smarter, but they have no native way to hold, send, or manage money on-chain. Existing wallets are built for humans.

**What AgentWallet does:**
- **PDA-enforced spending limits** — Solana itself rejects transactions that exceed limits, not some API server. Even if the agent gets prompt-injected, the chain says no.
- **Trustless escrow** — Agent A locks funds, Agent B delivers work, funds release. No middleman.
- **Agent marketplace** — Agents can discover and hire each other for tasks
- **Agent Commerce Protocol (ACP)** — 4-phase job lifecycle with signed memos for full audit trail

**Quick example with the Python SDK:**

```python
from agentwallet import AgentWalletClient

client = AgentWalletClient(api_key="your-key")

# Create an agent with a Solana wallet
agent = client.agents.create(name="trader-bot", type="trading")
wallet = client.wallets.create(agent_id=agent["id"], wallet_type="solana")

# Set spending limit — enforced on-chain
client.policies.create(
    agent_id=agent["id"],
    max_transaction=1.0,  # max 1 SOL per tx
    daily_limit=10.0       # max 10 SOL/day
)
```

**Tech stack:** FastAPI + Anchor/Rust + SQLAlchemy + 88+ endpoints, 110 tests passing

Live on devnet: https://api.agentwallet.fun/docs

Fully open source (MIT): https://github.com/YouthAIAgent/agentwallet

Would love feedback on the Anchor program design. What use cases would you build?

---

### r/LangChain

**Title:** `Gave my LangChain agents their own Solana wallets with spending limits, escrow, and an agent marketplace — open source`

**Body:**

Hey everyone,

I built **AgentWallet** — open-source infrastructure that gives AI agents their own wallets on Solana. Here's why this matters for LangChain builders:

**1. Agents can pay for things**
Your agent needs to call a paid API, buy data, or pay another agent? It has its own wallet now.

**2. Spending limits immune to prompt injection**
Limits are enforced on-chain by Solana itself. Even if someone tricks your agent via prompt injection, the blockchain rejects overspending.

**3. Agents can hire other agents**
Built-in marketplace + Agent Commerce Protocol. Your research agent can hire a data-scraping agent, negotiate price, pay through escrow, and evaluate the work — all programmatically.

**LangChain integration example:**

```python
from langchain.tools import tool
from agentwallet import AgentWalletClient

aw = AgentWalletClient(api_key="your-key")

@tool
def check_balance(wallet_id: str) -> str:
    """Check wallet balance on Solana"""
    b = aw.wallets.get_balance(wallet_id)
    return f"Balance: {b['balance']} SOL"

@tool
def pay_agent(to_wallet: str, amount: float) -> str:
    """Pay another agent via Solana transfer"""
    tx = aw.transactions.create(
        from_wallet=MY_WALLET_ID,
        to_wallet=to_wallet,
        amount=amount
    )
    return f"Paid {amount} SOL. TX: {tx['id']}"

@tool
def hire_agent(service_id: str) -> str:
    """Hire an agent from the marketplace"""
    job = aw.marketplace.create_job(service_id=service_id)
    return f"Hired! Job: {job['id']}"
```

**SDK:** `pip install aw-protocol-sdk`

**88+ API endpoints**, 110 tests, fully async, MIT licensed.

Live docs: https://api.agentwallet.fun/docs
GitHub: https://github.com/YouthAIAgent/agentwallet

What LangChain use cases would you build with financially autonomous agents?

---

### r/artificial

**Title:** `What happens when AI agents have their own wallets? I built the open-source infrastructure to find out.`

**Body:**

What if AI agents could hold money, negotiate prices, and pay each other — autonomously?

I built **AgentWallet** — open-source wallet infrastructure for AI agents on Solana. Here's what it enables:

**1. On-chain spending guardrails**
Agents have wallets with programmable spending limits enforced by the blockchain itself. Not by an API. Not by a server. By Solana. Even prompt injection can't bypass this.

**2. Trustless escrow**
Agent A wants to hire Agent B. Funds go into escrow. Agent B delivers. Funds release. If there's a dispute, an evaluator agent arbitrates. No humans needed.

**3. Agent marketplace**
Agents register their capabilities and pricing. Other agents browse, compare, and hire — like a freelancer marketplace, but fully autonomous.

**4. Agent Commerce Protocol**
Full 4-phase job lifecycle: request → negotiation → transaction → evaluation. Every step is signed for a cryptographic audit trail.

**5. Swarm coordination**
An orchestrator agent breaks complex tasks into subtasks, assigns them to worker agents, and each worker gets paid through policy-enforced wallets.

```python
from agentwallet import AgentWalletClient

client = AgentWalletClient(api_key="your-key")

# Create an agent with a wallet
agent = client.agents.create(name="researcher", type="research")
wallet = client.wallets.create(agent_id=agent["id"], wallet_type="solana")

# Set spending policy
client.policies.create(agent_id=agent["id"], max_transaction=1.0, daily_limit=10.0)

# Create escrow for a job
escrow = client.escrow.create(
    buyer_agent_id=agent["id"],
    seller_agent_id="seller-agent-id",
    amount=5.0
)
```

88+ API endpoints. 110 tests. Production-ready. MIT licensed.

Live API: https://api.agentwallet.fun/docs
GitHub: https://github.com/YouthAIAgent/agentwallet

The real question: what happens when agents start building economic relationships with each other? What use cases would you build?

---

## PART 2: AWESOME LIST TARGETS

| Priority | List | Repo | Target Section |
|----------|------|------|----------------|
| 1 | awesome-ai-agents | github.com/e2b-dev/awesome-ai-agents | Frameworks / Infrastructure |
| 2 | awesome-mcp-servers | github.com/punkpeye/awesome-mcp-servers | Finance / Blockchain |
| 3 | awesome-solana | github.com/anza-xyz/awesome-solana | Development Tools |
| 4 | awesome-langchain | github.com/kyrolabs/awesome-langchain | Tools / Integrations |
| 5 | awesome-fastapi | github.com/mjhea0/awesome-fastapi | Open Source Projects |
| 6 | awesome-web3 | github.com/ahmet/awesome-web3 | Infrastructure |
| 7 | awesome-autonomous-agents | github.com/oleksis/awesome-autonomous-agents | Agent Economy |
| 8 | awesome-python | github.com/vinta/awesome-python | Third-party APIs |
| 9 | awesome-solana-dev | github.com/nickvidal/awesome-solana-dev | Anchor Projects |
| 10 | awesome-defi | github.com/OffcierCia/DeFi-Developer-Road-Map | Tools and Utilities |

### Suggested entries per list:

**awesome-ai-agents:**
> [AgentWallet](https://github.com/YouthAIAgent/agentwallet) - Autonomous financial infrastructure for AI agents. Wallet-as-a-service with on-chain spending limits (Solana), trustless escrow, agent marketplace, and Agent Commerce Protocol. MIT licensed.

**awesome-mcp-servers:**
> [AgentWallet MCP](https://github.com/YouthAIAgent/agentwallet) - 33 MCP tools for AI agent financial operations on Solana — wallets, transfers, escrow, marketplace, spending policies.

**awesome-solana:**
> [AgentWallet](https://github.com/YouthAIAgent/agentwallet) - Open-source wallet infrastructure for AI agents on Solana. Anchor program with PDA-enforced spending limits, trustless escrow, agent marketplace, and Python SDK.

**awesome-langchain:**
> [AgentWallet](https://github.com/YouthAIAgent/agentwallet) - Give LangChain agents their own Solana wallets with spending limits, escrow payments, and an agent marketplace. Python SDK + MCP server with 33 AI-native tools.

**awesome-fastapi:**
> [AgentWallet](https://github.com/YouthAIAgent/agentwallet) - Production FastAPI app with 88+ endpoints for AI agent wallet infrastructure. Async SQLAlchemy, Redis caching, JWT + API key auth.

---

## PART 3: SUBMISSION CHECKLIST

For each awesome list PR:
1. Fork the repository
2. Add entry in appropriate section (alphabetical order)
3. PR title: "Add AgentWallet - AI agent wallet infrastructure on Solana"
4. PR body: explain what it does, why it fits, link to live deployment, note MIT license
5. Follow each list's CONTRIBUTING.md guidelines
