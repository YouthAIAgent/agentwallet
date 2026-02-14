# Agentic Commerce Protocol — Technical Architecture

> **"The full stack for AI agents to earn, spend, and trade autonomously."**

## The Vision

AgentWallet isn't just a wallet — it's the **financial operating system** for the agentic economy. Every layer of the stack exists to make one thing possible: **AI agents transacting autonomously, safely, at internet speed.**

---

## Tech Stack — 10 Layers

```
┌──────────────────────────────────────────────────────────────────┐
│                    AGENTIC COMMERCE STACK                         │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Layer 10: FOUNDATION MODEL                                │  │
│  │  GPT, Gemini, Llama — the agent's brain                     │  │
│  │  Decides WHAT to buy, sell, trade, pay                     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              ↕                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Layer 9: MCP (Model Context Protocol)                     │  │
│  │  27 AgentWallet tools — the agent's hands                  │  │
│  │  create_wallet, transfer_sol, create_escrow, etc.          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              ↕                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Layer 8: AGENT                                            │  │
│  │  Autonomous AI agent with identity + reputation            │  │
│  │  Registered on-chain, capabilities declared, scored        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              ↕                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Layer 7: FACILITATOR                                      │  │
│  │  AgentWallet Protocol — orchestrates everything            │  │
│  │  Policy engine, fee collection, escrow management          │  │
│  │  Compliance, analytics, audit trail                        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              ↕                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Layer 6: x402 (HTTP-Native Payments)                      │  │
│  │  HTTP 402 Payment Required → instant stablecoin payment    │  │
│  │  Zero friction, zero accounts, zero API keys               │  │
│  │  Agent hits endpoint → pays → gets access. Done.           │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              ↕                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Layer 5: UNIVERSAL BALANCE                                │  │
│  │  Unified balance across chains and tokens                  │  │
│  │  SOL + USDC + USDT + any SPL = one view                   │  │
│  │  Cross-chain balance aggregation (Solana + EVM L2s)        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              ↕                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Layer 4: ACCOUNT ABSTRACTION                              │  │
│  │  Agents don't manage private keys directly                 │  │
│  │  Smart wallet: gasless tx, batching, session keys          │  │
│  │  Programmable ownership — org controls, agent operates     │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              ↕                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Layer 3: STABLECOINS                                      │  │
│  │  USDC / USDT / PYUSD — the settlement layer               │  │
│  │  No volatility risk for commerce                           │  │
│  │  Instant finality, global, 24/7                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              ↕                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Layer 2: WALLETS                                          │  │
│  │  AgentWallet — per-agent Solana wallets                    │  │
│  │  Encrypted keys, spending limits, policies                 │  │
│  │  Keys never leave the server                               │  │
│  └────────────────────────────────────────────────────────────┘  │
│                              ↕                                   │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │  Layer 1: BLOCKCHAIN                                       │  │
│  │  Solana (primary) → EVM L2s (Arbitrum, Base, Polygon)      │  │
│  │  On-chain PDAs, escrow, settlement                         │  │
│  │  Immutable, trustless, permissionless                      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Layer Deep Dives

### Layer 1: Blockchain
**The Settlement Layer**

The immutable truth. Every transaction, escrow, and state change settles here.

| Chain | Role | Status |
|---|---|---|
| **Solana** | Primary — fast, cheap, agent-optimized | ✅ Devnet Live |
| **Base** | EVM L2 — Coinbase ecosystem, x402 native | 📋 Planned |
| **Arbitrum** | EVM L2 — DeFi liquidity | 📋 Planned |
| **Polygon** | EVM L2 — Enterprise adoption | 📋 Planned |

**Why multi-chain:** Agents operate across ecosystems. A trading agent on Solana might need to pay a data provider on Base. Universal settlement.

---

### Layer 2: Wallets
**The Identity Layer**

Every agent gets a dedicated wallet = on-chain identity.

```
Agent Created
    ↓
Keypair Generated (Ed25519 / secp256k1)
    ↓
Private Key Encrypted (Fernet dev / AWS KMS prod)
    ↓
Wallet PDA Created On-Chain
    ↓
Spending Limits Set (per-tx, daily, whitelist)
    ↓
Agent is financially autonomous
```

**Key properties:**
- Private keys NEVER exposed via API
- Per-agent isolation — one agent can't touch another's wallet
- Org-level oversight — human always has override
- Programmable limits — not just a wallet, a *policy-enforced* wallet

---

### Layer 3: Stablecoins
**The Value Layer**

Agents don't trade in volatile tokens for commerce — they use stablecoins.

| Stablecoin | Chain | Use Case |
|---|---|---|
| **USDC** | Solana, Base, Arbitrum | Primary settlement |
| **USDT** | Solana, Polygon | High-volume payments |
| **PYUSD** | Solana, Ethereum | PayPal ecosystem bridge |

**Why stablecoins for agents:**
- No volatility = predictable costs
- $1 in = $1 out (minus gas)
- 24/7 global settlement
- Programmable — smart contract native
- Perfect for micropayments (x402)

---

### Layer 4: Account Abstraction
**The UX Layer**

Agents shouldn't deal with gas, nonces, or raw signing. Account abstraction makes wallets programmable.

**Capabilities:**
- **Gasless transactions** — facilitator sponsors gas, deducts from agent balance
- **Session keys** — temporary keys with limited permissions for specific tasks
- **Batch operations** — multiple transfers in one atomic transaction
- **Programmable ownership** — org is owner, agent is operator
- **Recovery** — org can always recover/freeze agent wallets
- **Spending sessions** — "agent can spend up to 10 USDC in next 1 hour"

```
Traditional:    Agent → Sign TX → Pay Gas → Submit → Wait
With AA:        Agent → Call SDK → Done (gas abstracted, batched, policy-checked)
```

---

### Layer 5: Universal Balance
**The Aggregation Layer**

One agent. Multiple chains. Multiple tokens. One unified balance.

```json
{
    "agent": "trading-bot-alpha",
    "universal_balance": {
        "total_usd": 1547.32,
        "breakdown": {
            "solana": {
                "SOL": { "amount": 12.5, "usd": 1250.00 },
                "USDC": { "amount": 200.00, "usd": 200.00 }
            },
            "base": {
                "ETH": { "amount": 0.02, "usd": 47.32 },
                "USDC": { "amount": 50.00, "usd": 50.00 }
            }
        }
    }
}
```

**Features:**
- Real-time cross-chain balance aggregation
- Auto-conversion quotes (how much USDC on Base can I get for 1 SOL?)
- Unified spending limits across all chains
- Single analytics dashboard for all assets

---

### Layer 6: x402 — HTTP-Native Payments
**The Commerce Layer**

This is where it gets revolutionary. x402 turns every HTTP endpoint into a paywall that agents can pay instantly.

**Flow:**
```
1. Agent → GET /api/weather-data
2. Server → HTTP 402 Payment Required
   {
     "x402Version": 1,
     "accepts": [{
       "network": "solana",
       "token": "USDC",
       "amount": "0.001",
       "payTo": "merchant_address"
     }],
     "description": "Weather data API"
   }
3. Agent → Pays 0.001 USDC via AgentWallet
4. Agent → Retries GET /api/weather-data (with payment proof header)
5. Server → 200 OK + data
```

**AgentWallet x402 Integration:**
- Auto-detect 402 responses
- Auto-pay if within policy limits
- Track all x402 payments in audit log
- Budget enforcement — "max 5 USDC/day on API calls"
- Merchant discovery — find and pay any x402 endpoint

**Why this matters:** No API keys. No accounts. No subscriptions. Agent pays per-request with stablecoins. Instant. Permissionless. Internet-scale micropayments.

---

### Layer 7: Facilitator (AgentWallet Protocol)
**The Orchestration Layer**

The brain of the operation. Everything flows through here.

```
┌─ FACILITATOR ──────────────────────────────────────────┐
│                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │ Policy Engine │  │ Fee Collector │  │   Escrow     ││
│  │              │  │              │  │   Manager    ││
│  │ • Limits     │  │ • BPS fees   │  │              ││
│  │ • Whitelist  │  │ • Tier-based │  │ • Create     ││
│  │ • Blacklist  │  │ • Revenue    │  │ • Fund       ││
│  │ • Time gates │  │              │  │ • Release    ││
│  │ • Approvals  │  │              │  │ • Dispute    ││
│  └──────────────┘  └──────────────┘  └──────────────┘│
│                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐│
│  │  Compliance  │  │  Analytics   │  │   Agent      ││
│  │              │  │              │  │   Registry   ││
│  │ • Audit log  │  │ • Daily KPIs │  │              ││
│  │ • Anomalies  │  │ • Trends     │  │ • Identity   ││
│  │ • Reports    │  │ • Forecasts  │  │ • Reputation ││
│  │ • EU AI Act  │  │ • Exports    │  │ • Discovery  ││
│  └──────────────┘  └──────────────┘  └──────────────┘│
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Revenue model:** Basis-point fees on every transaction. More agents = more transactions = more revenue. Pure infrastructure play.

---

### Layer 8: Agent
**The Actor Layer**

An agent is a registered, on-chain entity with:
- **Identity** — unique ID, name, capabilities
- **Reputation** — score based on transaction history, escrow completion rate
- **Wallet(s)** — one or more funded wallets
- **Policies** — spending rules and limits
- **Capabilities** — declared abilities (trading, data, compute, etc.)

**Agent-to-Agent Commerce:**
```
Agent A (buyer)                    Agent B (seller)
    │                                    │
    ├─── Discover Agent B ──────────────►│
    │    (via registry/marketplace)       │
    │                                    │
    ├─── Create Escrow (2 USDC) ────────►│
    │    (funds locked on-chain)          │
    │                                    │
    │◄─── Deliver Service ──────────────┤
    │    (data, compute, analysis)        │
    │                                    │
    ├─── Release Escrow ────────────────►│
    │    (Agent B gets paid)              │
    │                                    │
    └─── Rate Agent B (reputation) ─────►│
```

---

### Layer 9: MCP (Model Context Protocol)
**The Interface Layer**

MCP is how foundation models actually USE the financial stack. 27 tools that turn any LLM into a financially autonomous agent.

```python
# Inside AI agent's tool use:
create_agent(name="research-bot", capabilities=["data", "payments"])
transfer_sol(from_wallet="...", to_address="...", amount_sol=0.5)
create_escrow(funder_wallet="...", recipient="...", amount_sol=2.0)
get_balance(wallet_id="...")
get_analytics_summary(days=30)
```

**Why MCP matters:**
- Standard protocol — works with ANY MCP-compatible model
- No custom integration per model
- Tools are discoverable — model sees what it can do
- Composable — chain multiple tools for complex workflows

---

### Layer 10: Foundation Model
**The Intelligence Layer**

The model decides. Everything else executes.

| Model | Role |
|---|---|
| **LLM** | Complex reasoning, escrow conditions, dispute resolution |
| **GPT** | Trading strategies, market analysis |
| **Gemini** | Multi-modal data processing, image analysis tasks |
| **Llama** | Cost-effective bulk operations, classification |

**The key insight:** Foundation models don't need to understand blockchain. They just need tools. MCP gives them tools. AgentWallet gives those tools teeth.

---

## The Full Transaction Flow

```
Foundation Model (LLM)
    │ "Pay 0.5 USDC to data-provider for weather API"
    ↓
MCP Layer
    │ transfer_sol(from_wallet, to_address, 0.5)
    ↓
Agent Layer
    │ Agent "weather-bot" authenticated, capabilities verified
    ↓
Facilitator
    │ Policy check → ALLOW
    │ Fee calculation → 0.005 USDC (1% BPS)
    ↓
x402 (if HTTP payment)
    │ HTTP 402 → auto-pay → retry with proof
    ↓
Universal Balance
    │ Debit 0.505 USDC from Solana USDC balance
    ↓
Account Abstraction
    │ Gasless tx, batched with fee transfer
    ↓
Stablecoin
    │ USDC transfer instruction
    ↓
Wallet
    │ Sign with encrypted key, submit
    ↓
Blockchain (Solana)
    │ Confirmed in ~400ms
    ↓
Audit Log
    │ Immutable record: who, what, when, how much
    ✓ DONE
```

---

## Implementation Phases

### Phase 1: Foundation ✅ (DONE)
- [x] Solana program (Anchor/Rust)
- [x] Wallet engine with encryption
- [x] Policy engine
- [x] Escrow service
- [x] REST API (FastAPI)
- [x] Python SDK on PyPI
- [x] MCP Server (27 tools) on PyPI
- [x] Dashboard (React)
- [x] CI/CD pipeline

### Phase 2: Commerce Layer (NEXT)
- [ ] x402 client integration in SDK
- [ ] x402 server middleware for API endpoints
- [ ] Stablecoin (USDC/USDT) transfer support
- [ ] Universal balance aggregation
- [ ] Agent-to-agent marketplace
- [ ] Reputation scoring system

### Phase 3: Abstraction Layer
- [ ] Account abstraction (gasless, session keys)
- [ ] Cross-chain bridging (Solana ↔ EVM)
- [ ] Multi-chain wallet support
- [ ] Gas sponsorship service

### Phase 4: Scale
- [ ] Mainnet deployment
- [ ] Agent discovery marketplace
- [ ] Payment streaming (continuous micropayments)
- [ ] On-chain reputation (Soulbound tokens)
- [ ] Enterprise tier (custom compliance, SLAs)

---

## Competitive Moat

| Feature | AgentWallet | Generic Wallets | Centralized APIs |
|---|---|---|---|
| Agent-native | ✅ | ❌ | ❌ |
| Programmable limits | ✅ | ❌ | Partial |
| On-chain escrow | ✅ | ❌ | ❌ |
| x402 integration | ✅ | ❌ | ❌ |
| MCP tools | ✅ | ❌ | ❌ |
| Multi-chain | 🔄 | Some | N/A |
| Compliance built-in | ✅ | ❌ | Varies |
| Open protocol | ✅ | Varies | ❌ |

---

*"Every AI agent deserves a wallet. Every wallet deserves limits. Every transaction deserves a trail. Every payment deserves to be instant."*

**— AgentWallet Protocol**
