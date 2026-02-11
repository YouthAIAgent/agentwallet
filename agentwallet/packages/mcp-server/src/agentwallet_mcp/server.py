"""AgentWallet MCP Server — Full wallet infrastructure as AI-native tools.

Exposes AgentWallet Protocol operations via the Model Context Protocol (MCP),
enabling any MCP-compatible AI agent (Claude, GPT, Gemini, etc.) to:
  - Create and manage agent wallets
  - Transfer SOL with policy enforcement
  - Create and manage trustless escrow
  - Query analytics and audit trails
  - Set spending policies and limits

Usage:
    # stdio transport (default for Claude Desktop / OpenClaw)
    AGENTWALLET_API_KEY=aw_live_xxx agentwallet-mcp

    # Or in Claude Desktop config:
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
"""

from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    TextContent,
    Tool,
)

from .api_client import AgentWalletClient, AgentWalletAPIError

logger = logging.getLogger("agentwallet-mcp")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ok(data: Any) -> list[TextContent]:
    """Wrap a dict/list as JSON text content."""
    return [TextContent(type="text", text=json.dumps(data, indent=2, default=str))]


def _err(msg: str) -> list[TextContent]:
    return [TextContent(type="text", text=json.dumps({"error": msg}))]


def _strip_none(d: dict) -> dict:
    """Remove None values from a dict before sending to API."""
    return {k: v for k, v in d.items() if v is not None}


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------

TOOLS: list[Tool] = [
    # ── Agents ─────────────────────────────────────────────────
    Tool(
        name="create_agent",
        description="Register a new AI agent and automatically create its Solana wallet. Returns agent details including wallet address.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Unique agent name (e.g. 'trading-bot-alpha')"},
                "description": {"type": "string", "description": "What this agent does"},
                "capabilities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Agent capabilities: trading, payments, escrow, analytics",
                },
                "is_public": {"type": "boolean", "description": "Whether this agent is publicly visible", "default": False},
            },
            "required": ["name"],
        },
    ),
    Tool(
        name="get_agent",
        description="Get details of a specific agent by ID, including status, reputation, and wallet info.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "Agent UUID"},
            },
            "required": ["agent_id"],
        },
    ),
    Tool(
        name="list_agents",
        description="List all registered AI agents. Optionally filter by status (active/paused/suspended).",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filter: active, paused, suspended"},
                "limit": {"type": "integer", "description": "Max results (default 50)", "default": 50},
                "offset": {"type": "integer", "description": "Pagination offset", "default": 0},
            },
        },
    ),
    Tool(
        name="update_agent",
        description="Update an agent's name, description, capabilities, or status.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "Agent UUID"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "status": {"type": "string", "description": "active, paused, or suspended"},
                "capabilities": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["agent_id"],
        },
    ),

    # ── Wallets ────────────────────────────────────────────────
    Tool(
        name="create_wallet",
        description="Create a new Solana wallet. Optionally link to an agent. Returns wallet address.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "Link wallet to this agent"},
                "wallet_type": {"type": "string", "description": "agent, treasury, or fee", "default": "agent"},
                "label": {"type": "string", "description": "Human-readable label"},
            },
        },
    ),
    Tool(
        name="get_wallet",
        description="Get wallet details including address and active status.",
        inputSchema={
            "type": "object",
            "properties": {
                "wallet_id": {"type": "string", "description": "Wallet UUID"},
            },
            "required": ["wallet_id"],
        },
    ),
    Tool(
        name="list_wallets",
        description="List all wallets. Optionally filter by agent or wallet type.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "string", "description": "Filter by agent"},
                "wallet_type": {"type": "string", "description": "Filter: agent, treasury, fee"},
                "limit": {"type": "integer", "default": 50},
                "offset": {"type": "integer", "default": 0},
            },
        },
    ),
    Tool(
        name="get_balance",
        description="Get SOL and SPL token balances for a wallet. Returns SOL balance and all token holdings.",
        inputSchema={
            "type": "object",
            "properties": {
                "wallet_id": {"type": "string", "description": "Wallet UUID"},
            },
            "required": ["wallet_id"],
        },
    ),

    # ── Tokens ─────────────────────────────────────────────────
    Tool(
        name="transfer_token",
        description="Send USDC or USDT from an agent wallet to a destination address. Enforces spending policies, deducts platform fees in SOL, and creates an audit trail.",
        inputSchema={
            "type": "object",
            "properties": {
                "from_wallet_id": {"type": "string", "description": "Source wallet UUID"},
                "to_address": {"type": "string", "description": "Destination Solana address (base58)"},
                "token_symbol": {"type": "string", "description": "Token symbol (USDC or USDT)"},
                "amount": {"type": "number", "description": "Amount in human-readable format (e.g. 10.50)"},
                "memo": {"type": "string", "description": "Transaction memo / reason"},
                "idempotency_key": {"type": "string", "description": "Unique key to prevent duplicate sends"},
            },
            "required": ["from_wallet_id", "to_address", "token_symbol", "amount"],
        },
    ),
    Tool(
        name="get_token_balances",
        description="Get all supported token balances (USDC, USDT) for a wallet, plus SOL balance.",
        inputSchema={
            "type": "object",
            "properties": {
                "wallet_id": {"type": "string", "description": "Wallet UUID"},
            },
            "required": ["wallet_id"],
        },
    ),
    Tool(
        name="list_supported_tokens",
        description="List all supported stablecoins with their mint addresses and decimals.",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),

    # ── Transactions ───────────────────────────────────────────
    Tool(
        name="transfer_sol",
        description="Send SOL from an agent wallet to a destination address. Enforces spending policies, deducts platform fees, and creates an audit trail. Returns transaction signature.",
        inputSchema={
            "type": "object",
            "properties": {
                "from_wallet": {"type": "string", "description": "Source wallet UUID"},
                "to_address": {"type": "string", "description": "Destination Solana address (base58)"},
                "amount_sol": {"type": "number", "description": "Amount in SOL (e.g. 0.5)"},
                "memo": {"type": "string", "description": "Transaction memo / reason"},
                "idempotency_key": {"type": "string", "description": "Unique key to prevent duplicate sends"},
            },
            "required": ["from_wallet", "to_address", "amount_sol"],
        },
    ),
    Tool(
        name="batch_transfer",
        description="Send SOL to multiple recipients in a single operation. Each transfer is policy-enforced independently.",
        inputSchema={
            "type": "object",
            "properties": {
                "transfers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "from_wallet_id": {"type": "string"},
                            "to_address": {"type": "string"},
                            "amount_sol": {"type": "number"},
                            "memo": {"type": "string"},
                        },
                        "required": ["from_wallet_id", "to_address", "amount_sol"],
                    },
                    "description": "Array of transfer objects",
                },
            },
            "required": ["transfers"],
        },
    ),
    Tool(
        name="get_transaction",
        description="Get full details of a transaction including status, signature, fees, and timestamps.",
        inputSchema={
            "type": "object",
            "properties": {
                "transaction_id": {"type": "string", "description": "Transaction UUID"},
            },
            "required": ["transaction_id"],
        },
    ),
    Tool(
        name="list_transactions",
        description="List transactions with optional filters. Returns transaction history for auditing.",
        inputSchema={
            "type": "object",
            "properties": {
                "agent_id": {"type": "string"},
                "wallet_id": {"type": "string"},
                "status": {"type": "string", "description": "pending, confirmed, failed"},
                "limit": {"type": "integer", "default": 50},
                "offset": {"type": "integer", "default": 0},
            },
        },
    ),

    # ── Escrow ─────────────────────────────────────────────────
    Tool(
        name="create_escrow",
        description="Create a trustless escrow for agent-to-agent task payments. Funds are locked on-chain in a PDA until released, refunded, or expired. Perfect for pay-for-task workflows.",
        inputSchema={
            "type": "object",
            "properties": {
                "funder_wallet": {"type": "string", "description": "Funder wallet UUID"},
                "recipient_address": {"type": "string", "description": "Recipient Solana address"},
                "amount_sol": {"type": "number", "description": "Amount to lock in escrow"},
                "arbiter_address": {"type": "string", "description": "Optional arbiter who can resolve disputes"},
                "conditions": {"type": "object", "description": "Task conditions / metadata"},
                "expires_in_hours": {"type": "integer", "description": "Auto-refund after N hours", "default": 24},
            },
            "required": ["funder_wallet", "recipient_address", "amount_sol"],
        },
    ),
    Tool(
        name="release_escrow",
        description="Release escrow funds to the recipient. Confirms task completion. Only funder or arbiter can release.",
        inputSchema={
            "type": "object",
            "properties": {
                "escrow_id": {"type": "string", "description": "Escrow UUID"},
            },
            "required": ["escrow_id"],
        },
    ),
    Tool(
        name="refund_escrow",
        description="Refund escrow funds back to the funder. Used when task was not completed.",
        inputSchema={
            "type": "object",
            "properties": {
                "escrow_id": {"type": "string", "description": "Escrow UUID"},
            },
            "required": ["escrow_id"],
        },
    ),
    Tool(
        name="dispute_escrow",
        description="Raise a dispute on an escrow. Requires arbiter resolution.",
        inputSchema={
            "type": "object",
            "properties": {
                "escrow_id": {"type": "string", "description": "Escrow UUID"},
                "reason": {"type": "string", "description": "Reason for dispute"},
            },
            "required": ["escrow_id", "reason"],
        },
    ),
    Tool(
        name="get_escrow",
        description="Get escrow details including status, amounts, and all parties.",
        inputSchema={
            "type": "object",
            "properties": {
                "escrow_id": {"type": "string", "description": "Escrow UUID"},
            },
            "required": ["escrow_id"],
        },
    ),
    Tool(
        name="list_escrows",
        description="List all escrows. Filter by status: created, funded, released, refunded, disputed, expired.",
        inputSchema={
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "limit": {"type": "integer", "default": 50},
                "offset": {"type": "integer", "default": 0},
            },
        },
    ),

    # ── Policies ───────────────────────────────────────────────
    Tool(
        name="create_policy",
        description="Create a spending policy with rules like spending_limit_lamports, daily_limit_lamports, destination_whitelist, time_window, require_approval_above. Policies are enforced on every transaction.",
        inputSchema={
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Policy name (e.g. 'Daily Cap')"},
                "rules": {
                    "type": "object",
                    "description": "Policy rules: spending_limit_lamports, daily_limit_lamports, destination_whitelist, destination_blacklist, token_whitelist, time_window, require_approval_above",
                },
                "scope_type": {"type": "string", "description": "org (applies to all) or agent (specific agent)", "default": "org"},
                "scope_id": {"type": "string", "description": "Agent ID if scope_type=agent"},
                "priority": {"type": "integer", "description": "Higher = evaluated first", "default": 100},
            },
            "required": ["name", "rules"],
        },
    ),
    Tool(
        name="list_policies",
        description="List all spending policies.",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 50},
                "offset": {"type": "integer", "default": 0},
            },
        },
    ),
    Tool(
        name="update_policy",
        description="Update a policy's rules, name, or priority.",
        inputSchema={
            "type": "object",
            "properties": {
                "policy_id": {"type": "string"},
                "name": {"type": "string"},
                "rules": {"type": "object"},
                "priority": {"type": "integer"},
                "enabled": {"type": "boolean"},
            },
            "required": ["policy_id"],
        },
    ),
    Tool(
        name="delete_policy",
        description="Delete a spending policy.",
        inputSchema={
            "type": "object",
            "properties": {
                "policy_id": {"type": "string"},
            },
            "required": ["policy_id"],
        },
    ),

    # ── Analytics ──────────────────────────────────────────────
    Tool(
        name="get_analytics_summary",
        description="Get organization-level analytics: total spend, fees, transaction counts, active agents, unique destinations.",
        inputSchema={
            "type": "object",
            "properties": {
                "days": {"type": "integer", "description": "Lookback period in days", "default": 30},
            },
        },
    ),
    Tool(
        name="get_daily_analytics",
        description="Get daily transaction and spending metrics. Useful for trend analysis and cost forecasting.",
        inputSchema={
            "type": "object",
            "properties": {
                "days": {"type": "integer", "default": 30},
                "agent_id": {"type": "string", "description": "Filter by specific agent"},
            },
        },
    ),
    Tool(
        name="get_agent_analytics",
        description="Get per-agent spending breakdowns and performance metrics.",
        inputSchema={
            "type": "object",
            "properties": {
                "days": {"type": "integer", "default": 30},
            },
        },
    ),

    # ── x402 Auto-Pay ──────────────────────────────────────────
    Tool(
        name="configure_x402_pricing",
        description="Configure x402 payment requirements for API endpoints. Set per-route pricing in SOL or USDC. When enabled, the server returns 402 Payment Required for matching routes without valid payment.",
        inputSchema={
            "type": "object",
            "properties": {
                "pricing": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "route_pattern": {"type": "string", "description": "Route pattern (e.g. '/api/data/*', exact path, or regex)"},
                            "method": {"type": "string", "description": "HTTP method (* for all)", "default": "*"},
                            "price_lamports": {"type": "integer", "description": "Price in lamports (SOL)"},
                            "price_usdc": {"type": "number", "description": "Price in USDC"},
                            "description": {"type": "string", "description": "Human-readable description"},
                            "pay_to": {"type": "string", "description": "Solana address to receive payments"},
                            "max_deadline_seconds": {"type": "integer", "description": "Max seconds for payment validity", "default": 60},
                        },
                        "required": ["route_pattern", "pay_to"],
                    },
                    "description": "List of route pricing entries",
                },
                "enabled": {"type": "boolean", "description": "Enable/disable x402 middleware", "default": True},
                "network": {"type": "string", "description": "Solana network (solana-mainnet, solana-devnet)", "default": "solana-mainnet"},
                "default_pay_to": {"type": "string", "description": "Default payment address if not set per route"},
            },
            "required": ["pricing"],
        },
    ),
    Tool(
        name="get_x402_status",
        description="Check x402 configuration and payment history. Returns current pricing rules, enabled status, and payment stats.",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
    Tool(
        name="make_x402_request",
        description="Make an HTTP request with automatic x402 payment. If the server returns 402 Payment Required, automatically creates a Solana payment and retries with proof. Supports SOL and USDC payments.",
        inputSchema={
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to request"},
                "method": {"type": "string", "description": "HTTP method (GET, POST, etc.)", "default": "GET"},
                "headers": {"type": "object", "description": "Additional request headers", "default": {}},
                "body": {"type": "string", "description": "Request body (for POST/PUT)"},
                "wallet_id": {"type": "string", "description": "Wallet UUID to pay from"},
                "max_amount_lamports": {"type": "integer", "description": "Maximum lamports willing to pay per request"},
                "max_amount_usdc": {"type": "number", "description": "Maximum USDC willing to pay per request"},
            },
            "required": ["url", "wallet_id"],
        },
    ),

    # ── Compliance ─────────────────────────────────────────────
    Tool(
        name="get_audit_log",
        description="Get the immutable audit trail. Every state change in the system is logged here. Essential for compliance.",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 50},
            },
        },
    ),
    Tool(
        name="get_anomalies",
        description="Get detected anomalies: velocity spikes, unusual amounts, high failure rates.",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
]


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------

async def handle_tool(client: AgentWalletClient, name: str, args: dict) -> list[TextContent]:
    """Route tool call to the appropriate API endpoint."""
    try:
        match name:
            # Agents
            case "create_agent":
                data = await client.post("/agents", json=_strip_none({
                    "name": args["name"],
                    "description": args.get("description"),
                    "capabilities": args.get("capabilities", []),
                    "is_public": args.get("is_public", False),
                    "metadata": {},
                }))
                return _ok(data)

            case "get_agent":
                data = await client.get(f"/agents/{args['agent_id']}")
                return _ok(data)

            case "list_agents":
                params = _strip_none({
                    "status": args.get("status"),
                    "limit": args.get("limit", 50),
                    "offset": args.get("offset", 0),
                })
                data = await client.get("/agents", params=params)
                return _ok(data)

            case "update_agent":
                aid = args.pop("agent_id")
                data = await client.patch(f"/agents/{aid}", json=_strip_none(args))
                return _ok(data)

            # Wallets
            case "create_wallet":
                data = await client.post("/wallets", json=_strip_none({
                    "agent_id": args.get("agent_id"),
                    "wallet_type": args.get("wallet_type", "agent"),
                    "label": args.get("label"),
                }))
                return _ok(data)

            case "get_wallet":
                data = await client.get(f"/wallets/{args['wallet_id']}")
                return _ok(data)

            case "list_wallets":
                params = _strip_none({
                    "agent_id": args.get("agent_id"),
                    "wallet_type": args.get("wallet_type"),
                    "limit": args.get("limit", 50),
                    "offset": args.get("offset", 0),
                })
                data = await client.get("/wallets", params=params)
                return _ok(data)

            case "get_balance":
                data = await client.get(f"/wallets/{args['wallet_id']}/balance")
                return _ok(data)

            # Tokens
            case "transfer_token":
                data = await client.post("/tokens/transfer", json=_strip_none({
                    "from_wallet_id": args["from_wallet_id"],
                    "to_address": args["to_address"],
                    "token_symbol": args["token_symbol"],
                    "amount": args["amount"],
                    "memo": args.get("memo"),
                    "idempotency_key": args.get("idempotency_key"),
                }))
                return _ok(data)

            case "get_token_balances":
                data = await client.get(f"/tokens/balances/{args['wallet_id']}")
                return _ok(data)

            case "list_supported_tokens":
                data = await client.get("/tokens/supported")
                return _ok(data)

            # Transactions
            case "transfer_sol":
                data = await client.post("/transactions/transfer-sol", json=_strip_none({
                    "from_wallet_id": args["from_wallet"],
                    "to_address": args["to_address"],
                    "amount_sol": args["amount_sol"],
                    "memo": args.get("memo"),
                    "idempotency_key": args.get("idempotency_key"),
                }))
                return _ok(data)

            case "batch_transfer":
                data = await client.post("/transactions/batch-transfer", json={
                    "transfers": args["transfers"],
                })
                return _ok(data)

            case "get_transaction":
                data = await client.get(f"/transactions/{args['transaction_id']}")
                return _ok(data)

            case "list_transactions":
                params = _strip_none({
                    "agent_id": args.get("agent_id"),
                    "wallet_id": args.get("wallet_id"),
                    "status": args.get("status"),
                    "limit": args.get("limit", 50),
                    "offset": args.get("offset", 0),
                })
                data = await client.get("/transactions", params=params)
                return _ok(data)

            # Escrow
            case "create_escrow":
                data = await client.post("/escrow", json=_strip_none({
                    "funder_wallet_id": args["funder_wallet"],
                    "recipient_address": args["recipient_address"],
                    "amount_sol": args["amount_sol"],
                    "arbiter_address": args.get("arbiter_address"),
                    "conditions": args.get("conditions", {}),
                    "expires_in_hours": args.get("expires_in_hours", 24),
                }))
                return _ok(data)

            case "release_escrow":
                data = await client.post(f"/escrow/{args['escrow_id']}/action", json={"action": "release"})
                return _ok(data)

            case "refund_escrow":
                data = await client.post(f"/escrow/{args['escrow_id']}/action", json={"action": "refund"})
                return _ok(data)

            case "dispute_escrow":
                data = await client.post(f"/escrow/{args['escrow_id']}/action", json={
                    "action": "dispute",
                    "reason": args["reason"],
                })
                return _ok(data)

            case "get_escrow":
                data = await client.get(f"/escrow/{args['escrow_id']}")
                return _ok(data)

            case "list_escrows":
                params = _strip_none({
                    "status": args.get("status"),
                    "limit": args.get("limit", 50),
                    "offset": args.get("offset", 0),
                })
                data = await client.get("/escrow", params=params)
                return _ok(data)

            # Policies
            case "create_policy":
                data = await client.post("/policies", json=_strip_none({
                    "name": args["name"],
                    "rules": args["rules"],
                    "scope_type": args.get("scope_type", "org"),
                    "scope_id": args.get("scope_id"),
                    "priority": args.get("priority", 100),
                }))
                return _ok(data)

            case "list_policies":
                data = await client.get("/policies", params={
                    "limit": args.get("limit", 50),
                    "offset": args.get("offset", 0),
                })
                return _ok(data)

            case "update_policy":
                pid = args.pop("policy_id")
                data = await client.patch(f"/policies/{pid}", json=_strip_none(args))
                return _ok(data)

            case "delete_policy":
                await client.delete(f"/policies/{args['policy_id']}")
                return _ok({"deleted": True, "policy_id": args["policy_id"]})

            # Analytics
            case "get_analytics_summary":
                data = await client.get("/analytics/summary", params={"days": args.get("days", 30)})
                return _ok(data)

            case "get_daily_analytics":
                params = _strip_none({
                    "days": args.get("days", 30),
                    "agent_id": args.get("agent_id"),
                })
                data = await client.get("/analytics/daily", params=params)
                return _ok(data)

            case "get_agent_analytics":
                data = await client.get("/analytics/agents", params={"days": args.get("days", 30)})
                return _ok(data)

            # x402 Auto-Pay
            case "configure_x402_pricing":
                data = await client.post("/x402/configure", json=_strip_none({
                    "pricing": args["pricing"],
                    "enabled": args.get("enabled", True),
                    "network": args.get("network", "solana-mainnet"),
                    "default_pay_to": args.get("default_pay_to"),
                }))
                return _ok(data)

            case "get_x402_status":
                data = await client.get("/x402/status")
                return _ok(data)

            case "make_x402_request":
                data = await client.post("/x402/request", json=_strip_none({
                    "url": args["url"],
                    "method": args.get("method", "GET"),
                    "headers": args.get("headers", {}),
                    "body": args.get("body"),
                    "wallet_id": args["wallet_id"],
                    "max_amount_lamports": args.get("max_amount_lamports"),
                    "max_amount_usdc": args.get("max_amount_usdc"),
                }))
                return _ok(data)

            # Compliance
            case "get_audit_log":
                data = await client.get("/compliance/audit-log", params={"limit": args.get("limit", 50)})
                return _ok(data)

            case "get_anomalies":
                data = await client.get("/compliance/anomalies")
                return _ok(data)

            case _:
                return _err(f"Unknown tool: {name}")

    except AgentWalletAPIError as e:
        return _err(f"AgentWallet API error: {e.detail} (HTTP {e.status_code})")
    except Exception as e:
        logger.exception("Tool execution failed")
        return _err(f"Unexpected error: {str(e)}")


# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------

def create_server() -> Server:
    """Create and configure the MCP server."""
    server = Server("agentwallet-mcp")
    client = AgentWalletClient()

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        return await handle_tool(client, name, arguments)

    return server


def main():
    """Entry point for the MCP server (stdio transport)."""
    import asyncio

    async def run():
        server = create_server()
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())

    asyncio.run(run())


if __name__ == "__main__":
    main()
