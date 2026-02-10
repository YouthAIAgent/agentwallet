"""AgentWallet Operator CLI -- Manage and monitor the AgentWallet Protocol.

Usage:
    python -m agentwallet_cli.main status          Show platform overview
    python -m agentwallet_cli.main agents           List registered agents
    python -m agentwallet_cli.main wallets          List wallets with balances
    python -m agentwallet_cli.main transactions     List recent transactions
    python -m agentwallet_cli.main escrows          List escrows
    python -m agentwallet_cli.main config           Show current configuration

Global flags:
    --json      Output raw JSON instead of formatted tables
    --limit N   Max items to retrieve (default 50)

Environment variables:
    AGENTWALLET_API_URL   Base URL of the API (default http://localhost:8000)
    AGENTWALLET_API_KEY   API key for authentication
"""

import argparse
import json
import os
import sys

import httpx

# ── Configuration ────────────────────────────────────────────────

API_URL = os.environ.get("AGENTWALLET_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("AGENTWALLET_API_KEY", "")


def _headers() -> dict:
    """Build request headers with authentication."""
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["Authorization"] = f"Bearer {API_KEY}"
    return h


def _get(path: str, params: dict | None = None) -> dict:
    """Perform a synchronous GET request against the AgentWallet API."""
    url = f"{API_URL.rstrip('/')}{path}"
    try:
        resp = httpx.get(url, headers=_headers(), params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        print(f"ERROR: Could not connect to {url}")
        print("       Is the AgentWallet API running?")
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"ERROR: API returned {e.response.status_code}")
        try:
            detail = e.response.json()
            print(f"       {json.dumps(detail, indent=2)}")
        except Exception:
            print(f"       {e.response.text[:200]}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def _print_json(data):
    """Pretty-print JSON to stdout."""
    print(json.dumps(data, indent=2, default=str))


def _lamports_to_sol(lamports: int) -> str:
    """Convert lamports to a human-readable SOL string."""
    sol = lamports / 1e9
    if sol == 0:
        return "0"
    return f"{sol:.6f}"


def _truncate(s: str, length: int = 20) -> str:
    """Truncate a string with ellipsis if too long."""
    if not s:
        return ""
    if len(s) <= length:
        return s
    return s[: length - 3] + "..."


# ── Commands ─────────────────────────────────────────────────────

def cmd_status(args):
    """Show platform overview from /v1/analytics/summary."""
    data = _get("/v1/analytics/summary", params={"days": 30})

    if args.json:
        _print_json(data)
        return

    total_spend = _lamports_to_sol(data.get("total_spend_lamports", 0))
    total_fees = _lamports_to_sol(data.get("total_fees_lamports", 0))
    tx_count = data.get("tx_count", 0)
    failed = data.get("failed_tx_count", 0)
    active = data.get("active_agents", 0)
    destinations = data.get("unique_destinations", 0)
    period_start = data.get("period_start", "?")
    period_end = data.get("period_end", "?")

    print()
    print("=" * 60)
    print("  AGENTWALLET PLATFORM STATUS")
    print("=" * 60)
    print(f"  Period:              {period_start} -> {period_end}")
    print(f"  Active Agents:       {active}")
    print(f"  Total Transactions:  {tx_count}")
    print(f"  Failed Transactions: {failed}")
    print(f"  Total Spend:         {total_spend} SOL")
    print(f"  Total Fees:          {total_fees} SOL")
    print(f"  Unique Destinations: {destinations}")
    print("=" * 60)
    print()


def cmd_agents(args):
    """List registered agents from /v1/agents."""
    data = _get("/v1/agents", params={"limit": args.limit, "offset": 0})

    if args.json:
        _print_json(data)
        return

    agents = data.get("data", [])
    total = data.get("total", len(agents))

    print()
    print(f"  AGENTS ({total} total)")
    print("  " + "-" * 90)
    print(
        f"  {'Name':<22} {'Status':<10} {'Reputation':<12} {'Wallet ID':<24} "
        f"{'Public':<8} {'Created':<20}"
    )
    print("  " + "-" * 90)

    for a in agents:
        name = _truncate(a.get("name", "?"), 20)
        status = a.get("status", "?")
        rep = f"{a.get('reputation_score', 0):.1f}"
        wallet_id = str(a.get("default_wallet_id", ""))[:22] or "--"
        public = "Yes" if a.get("is_public") else "No"
        created = a.get("created_at", "?")[:19]

        print(f"  {name:<22} {status:<10} {rep:<12} {wallet_id:<24} {public:<8} {created:<20}")

    print("  " + "-" * 90)
    if len(agents) < total:
        print(f"  Showing {len(agents)} of {total}. Use --limit to see more.")
    print()


def cmd_wallets(args):
    """List wallets from /v1/wallets."""
    data = _get("/v1/wallets", params={"limit": args.limit, "offset": 0})

    if args.json:
        _print_json(data)
        return

    wallets = data.get("data", [])
    total = data.get("total", len(wallets))

    print()
    print(f"  WALLETS ({total} total)")
    print("  " + "-" * 100)
    print(
        f"  {'Label':<20} {'Type':<10} {'Address':<46} {'Active':<8} {'Created':<20}"
    )
    print("  " + "-" * 100)

    for w in wallets:
        label = _truncate(w.get("label", "") or "--", 18)
        wtype = w.get("wallet_type", "?")
        addr = w.get("address", "?")
        active = "Yes" if w.get("is_active") else "No"
        created = w.get("created_at", "?")[:19]

        print(f"  {label:<20} {wtype:<10} {addr:<46} {active:<8} {created:<20}")

    print("  " + "-" * 100)
    if len(wallets) < total:
        print(f"  Showing {len(wallets)} of {total}. Use --limit to see more.")
    print()


def cmd_transactions(args):
    """List recent transactions from /v1/transactions."""
    params = {"limit": args.limit, "offset": 0}
    data = _get("/v1/transactions", params=params)

    if args.json:
        _print_json(data)
        return

    txs = data.get("data", [])
    total = data.get("total", len(txs))

    print()
    print(f"  TRANSACTIONS ({total} total)")
    print("  " + "-" * 110)
    print(
        f"  {'ID':<10} {'Type':<12} {'Status':<12} {'Amount (SOL)':<14} "
        f"{'Fee (SOL)':<12} {'To':<24} {'Created':<20}"
    )
    print("  " + "-" * 110)

    for tx in txs:
        tx_id = str(tx.get("id", ""))[:8] + ".."
        tx_type = tx.get("tx_type", "?")
        status = tx.get("status", "?")
        amount = _lamports_to_sol(tx.get("amount_lamports", 0))
        fee = _lamports_to_sol(tx.get("platform_fee_lamports", 0))
        to_addr = _truncate(tx.get("to_address", "?"), 22)
        created = tx.get("created_at", "?")[:19]

        # Color indicators for terminal
        if status == "confirmed":
            status_display = status
        elif status == "failed":
            status_display = status
        elif status == "pending":
            status_display = status
        else:
            status_display = status

        print(
            f"  {tx_id:<10} {tx_type:<12} {status_display:<12} {amount:<14} "
            f"{fee:<12} {to_addr:<24} {created:<20}"
        )

    print("  " + "-" * 110)
    if len(txs) < total:
        print(f"  Showing {len(txs)} of {total}. Use --limit to see more.")
    print()


def cmd_escrows(args):
    """List escrows from /v1/escrow."""
    data = _get("/v1/escrow", params={"limit": args.limit, "offset": 0})

    if args.json:
        _print_json(data)
        return

    escrows = data.get("data", [])
    total = data.get("total", len(escrows))

    print()
    print(f"  ESCROWS ({total} total)")
    print("  " + "-" * 105)
    print(
        f"  {'ID':<10} {'Status':<12} {'Amount (SOL)':<14} "
        f"{'Recipient':<24} {'Expires':<20} {'Created':<20}"
    )
    print("  " + "-" * 105)

    for e in escrows:
        eid = str(e.get("id", ""))[:8] + ".."
        status = e.get("status", "?")
        amount = _lamports_to_sol(e.get("amount_lamports", 0))
        recipient = _truncate(e.get("recipient_address", "?"), 22)
        expires = (e.get("expires_at") or "--")[:19]
        created = e.get("created_at", "?")[:19]

        print(
            f"  {eid:<10} {status:<12} {amount:<14} "
            f"{recipient:<24} {expires:<20} {created:<20}"
        )

    print("  " + "-" * 105)
    if len(escrows) < total:
        print(f"  Showing {len(escrows)} of {total}. Use --limit to see more.")
    print()


def cmd_config(args):
    """Show current CLI configuration."""
    masked_key = ""
    if API_KEY:
        if len(API_KEY) > 8:
            masked_key = API_KEY[:4] + "****" + API_KEY[-4:]
        else:
            masked_key = "****"
    else:
        masked_key = "(not set)"

    config = {
        "api_url": API_URL,
        "api_key": masked_key,
        "api_key_set": bool(API_KEY),
    }

    if args.json:
        _print_json(config)
        return

    # Also check health endpoint
    health_status = "unknown"
    api_version = "?"
    try:
        health = _get("/health")
        health_status = health.get("status", "unknown")
        api_version = health.get("version", "?")
    except SystemExit:
        health_status = "unreachable"

    print()
    print("=" * 50)
    print("  AGENTWALLET CLI CONFIGURATION")
    print("=" * 50)
    print(f"  API URL:      {API_URL}")
    print(f"  API Key:      {masked_key}")
    print(f"  API Status:   {health_status}")
    print(f"  API Version:  {api_version}")
    print()
    print("  Environment Variables:")
    print(f"    AGENTWALLET_API_URL = {os.environ.get('AGENTWALLET_API_URL', '(not set, using default)')}")
    print(f"    AGENTWALLET_API_KEY = {'(set)' if API_KEY else '(not set)'}")
    print("=" * 50)
    print()


# ── CLI Entry Point ──────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="agentwallet",
        description="AgentWallet Operator CLI -- Manage and monitor the AgentWallet Protocol",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=False,
        help="Output raw JSON instead of formatted tables",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max items to retrieve (default: 50)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    subparsers.add_parser("status", help="Show platform overview (analytics summary)")
    subparsers.add_parser("agents", help="List registered AI agents")
    subparsers.add_parser("wallets", help="List wallets with balances")
    subparsers.add_parser("transactions", help="List recent transactions")
    subparsers.add_parser("escrows", help="List escrows")
    subparsers.add_parser("config", help="Show current configuration")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "status": cmd_status,
        "agents": cmd_agents,
        "wallets": cmd_wallets,
        "transactions": cmd_transactions,
        "escrows": cmd_escrows,
        "config": cmd_config,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
