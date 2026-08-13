# 🔥 aw-e2e — AgentWallet Testnet Test in One Command

Colorful hacker-style CLI that runs the full AgentWallet stack end to end:

```
register → api-key → agent → wallets → balance → escrow → transactions → x402 → billing
```

## One-liner (no install)

```bash
npx aw-e2e
```

Or straight from the repo:

```bash
node packages/cli-e2e/e2e.mjs
```

## Point it anywhere

```bash
npx aw-e2e --api https://api.agentwallet.fun     # hosted instance
npx aw-e2e --api http://localhost:8000            # local docker stack
```

## Requirements

- Node.js 18+ (for `npx` path)
- A running AgentWallet API (`docker compose up -d` for local)

## Exit codes

- `0` — every check passed
- `1` — one or more checks failed

## What it verifies

| Step | Checks |
|---|---|
| Health | `/health` returns ok |
| Register | fresh org + JWT |
| API key | scoped key (wallets/agents/escrows/billing/x402) |
| Agent | agent creation |
| Wallets | funder + recipient wallets |
| Balance | balance endpoint |
| Escrow | create + fetch by id |
| Transactions | list endpoint |
| x402 | configure paywall + status (disabled afterwards) |
| Billing | plans endpoint |

## Env vars

- `AGW_API_URL` — same as `--api`
