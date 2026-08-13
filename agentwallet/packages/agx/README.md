# 🤖 AGX — Agent Genesis Terminal Agent

A **Claude Code-style** AI agent that runs in your terminal with its **own Solana wallet**.

You bring the API provider. The agent brings its wallet.

```
npx agx
```

## Quick start

```bash
# 1. Point at any Anthropic-compatible provider (default: api.anthropic.com)
export AGX_API_KEY=sk-ant-...

# 2. Point at any OpenAI-compatible provider instead
export AGX_API_FORMAT=openai
export AGX_API_BASE=https://api.openai.com/v1
export AGX_API_KEY=sk-...

# 3. Run
node agx.mjs
```

On first launch AGX registers a **fresh org + agent + Solana wallet** with
AgentWallet (default `http://localhost:8000` — start it with
`docker compose up -d`). Identity is saved to `~/.agx/identity.json`.

## What it can do

**Coding (Claude Code style)**
- `read_file` / `write_file` — read & edit files on disk
- `run_command` — execute shell commands (asks for confirmation first)
- Streaming responses, multi-turn tool loop

**On-chain (wallet infrastructure)**
- `wallet_balance` — check SOL + token balance
- `send_sol` — send SOL to any address
- `create_escrow` — lock funds payable on completion
- `x402 pay-per-use` — pay for each API request on-chain (`/pay` or `AGX_PAY_PER_USE=1`)

**Agent Genesis organizations** (requires `pip install -e agent_genesis`)
- `genesis_design` — design an agent organization from a task (roles, runtimes, topology)
- `genesis_deploy` — deploy a designed organization to its target runtimes
- `genesis_orgs` — list organizations saved in Agent Genesis memory

## Slash commands

| Command | What it does |
|---|---|
| `/help` | show help |
| `/wallet` | wallet identity + balance |
| `/pay` | toggle x402 pay-per-use |
| `/model <name>` | switch model |
| `/quit` | exit |

## Env vars

| Var | Default | Meaning |
|---|---|---|
| `AGX_API_KEY` | — | provider key (required) |
| `AGX_API_BASE` | `https://api.anthropic.com` | provider base URL |
| `AGX_API_FORMAT` | `anthropic` | `anthropic` or `openai` |
| `AGX_MODEL` | `claude-sonnet-4-5` / `gpt-4o` | model name |
| `AGW_API_URL` | `http://localhost:8000` | AgentWallet API |
| `AGX_PAY_PER_USE` | off | x402 on-chain payment per request |
| `AGX_MAX_TOOL_TURNS` | `12` | tool-loop budget per message |

## Why decentralized?

AGX isn't a thin wrapper — every agent has:
- a **real Solana identity** (keypair held by AgentWallet, KMS-encrypted)
- **spending policy + audit trail** on every transaction
- **escrow-backed** agent-to-agent commerce
- **x402 pay-per-use** — no subscriptions, pay per request on-chain
