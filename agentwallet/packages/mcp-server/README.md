# AgentWallet MCP Server

**Give any AI agent a Solana wallet in one tool call.**

MCP (Model Context Protocol) server that exposes the full AgentWallet Protocol as AI-native tools. Works with any MCP-compatible client including desktop apps, IDEs, and agent frameworks.

## Quick Start

```bash
pip install agentwallet-mcp
```

### MCP Desktop Client

Add to your MCP client config:

```json
{
    "mcpServers": {
        "agentwallet": {
            "command": "agentwallet-mcp",
            "env": {
                "AGENTWALLET_API_KEY": "aw_live_xxx",
                "AGENTWALLET_BASE_URL": "https://your-api.up.railway.app/v1"
            }
        }
    }
}
```

### OpenClaw

Add to your OpenClaw config:

```json
{
    "mcp": {
        "agentwallet": {
            "command": "agentwallet-mcp",
            "env": {
                "AGENTWALLET_API_KEY": "aw_live_xxx",
                "AGENTWALLET_BASE_URL": "https://your-api.up.railway.app/v1"
            }
        }
    }
}
```

## Available Tools (26 tools)

### Agents
| Tool | Description |
|---|---|
| `create_agent` | Register an AI agent + auto-create its wallet |
| `get_agent` | Get agent details by ID |
| `list_agents` | List all agents (filter by status) |
| `update_agent` | Update agent name, status, capabilities |

### Wallets
| Tool | Description |
|---|---|
| `create_wallet` | Create a new Solana wallet |
| `get_wallet` | Get wallet details |
| `list_wallets` | List wallets (filter by agent/type) |
| `get_balance` | Get SOL + token balances |

### Transactions
| Tool | Description |
|---|---|
| `transfer_sol` | Send SOL (policy-enforced, fee-deducted, audited) |
| `batch_transfer` | Batch SOL transfers |
| `get_transaction` | Get transaction details |
| `list_transactions` | Transaction history |

### Escrow
| Tool | Description |
|---|---|
| `create_escrow` | Lock funds for agent-to-agent tasks |
| `release_escrow` | Release funds on task completion |
| `refund_escrow` | Refund if task not completed |
| `dispute_escrow` | Raise a dispute |
| `get_escrow` | Get escrow details |
| `list_escrows` | List all escrows |

### Policies
| Tool | Description |
|---|---|
| `create_policy` | Set spending limits, whitelists, time windows |
| `list_policies` | List all policies |
| `update_policy` | Modify policy rules |
| `delete_policy` | Remove a policy |

### Analytics & Compliance
| Tool | Description |
|---|---|
| `get_analytics_summary` | Org-level spending overview |
| `get_daily_analytics` | Daily metrics and trends |
| `get_agent_analytics` | Per-agent breakdowns |
| `get_audit_log` | Immutable audit trail |
| `get_anomalies` | Detected anomalies |

## Example Conversations

**User:** "Create a trading bot agent and give it a 10 SOL daily limit"

**AI Agent:**
1. Calls `create_agent(name="trading-bot", capabilities=["trading"])`
2. Calls `create_policy(name="Daily Cap", rules={"daily_limit_lamports": 10000000000}, scope_type="agent", scope_id="<agent_id>")`

**User:** "Set up an escrow — pay 2 SOL to worker-bot when it finishes the data analysis"

**AI Agent:**
1. Calls `create_escrow(funder_wallet="...", recipient_address="...", amount_sol=2.0, conditions={"task": "data-analysis"})`
2. Later: `release_escrow(escrow_id="...")` when task completes

## Environment Variables

| Variable | Required | Default | Description |
|---|:---:|---|---|
| `AGENTWALLET_API_KEY` | Yes | -- | Your API key (`aw_live_xxx`) |
| `AGENTWALLET_BASE_URL` | No | `http://localhost:8000/v1` | API endpoint |

## License

MIT — Build the agentic economy.
