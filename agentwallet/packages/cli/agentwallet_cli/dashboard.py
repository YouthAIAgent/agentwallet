"""AgentWallet Operator Dashboard -- Rich-based live monitoring.

Usage:
    python -m agentwallet_cli.dashboard              Launch live dashboard
    python -m agentwallet_cli.dashboard --interval 10 Refresh every 10 seconds

Environment variables:
    AGENTWALLET_API_URL   Base URL of the API (default http://localhost:8000)
    AGENTWALLET_API_KEY   API key for authentication
"""

import os
import sys
import time
from datetime import datetime

# Fix Windows encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import httpx
from rich import box
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# ── Configuration ────────────────────────────────────────────────

API_URL = os.environ.get("AGENTWALLET_API_URL", "http://localhost:8000")
API_KEY = os.environ.get("AGENTWALLET_API_KEY", "")
DEFAULT_REFRESH_INTERVAL = 5


def _headers() -> dict:
    """Build request headers with authentication."""
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["Authorization"] = f"Bearer {API_KEY}"
    return h


# ── API Polling ──────────────────────────────────────────────────

def _safe_get(client: httpx.Client, path: str, params: dict | None = None) -> dict | None:
    """Perform a GET request, returning None on any failure."""
    url = f"{API_URL.rstrip('/')}{path}"
    try:
        resp = client.get(url, headers=_headers(), params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        return None
    except Exception:
        return None


def poll_data(client: httpx.Client) -> dict:
    """Fetch all data needed for the dashboard in one pass."""
    summary = _safe_get(client, "/v1/analytics/summary", {"days": 30})
    agents = _safe_get(client, "/v1/agents", {"limit": 50})
    wallets = _safe_get(client, "/v1/wallets", {"limit": 100})
    transactions = _safe_get(client, "/v1/transactions", {"limit": 10})
    escrows = _safe_get(client, "/v1/escrow", {"limit": 50})
    health = _safe_get(client, "/health")

    return {
        "summary": summary,
        "agents": agents,
        "wallets": wallets,
        "transactions": transactions,
        "escrows": escrows,
        "health": health,
        "fetched_at": datetime.now(),
    }


# ── Helpers ──────────────────────────────────────────────────────

def _lamports_to_sol(lamports: int) -> str:
    """Convert lamports to SOL display string."""
    sol = lamports / 1e9
    if sol == 0:
        return "0"
    return f"{sol:.6f}"


def _short_id(uid: str) -> str:
    """Shorten a UUID for display."""
    if not uid:
        return "--"
    s = str(uid)
    if len(s) > 8:
        return s[:8]
    return s


def _short_addr(addr: str, length: int = 16) -> str:
    """Shorten a Solana address for display."""
    if not addr:
        return "--"
    if len(addr) <= length:
        return addr
    half = (length - 2) // 2
    return addr[:half] + ".." + addr[-half:]


def _status_style(status: str) -> str:
    """Return a Rich style string for a given status."""
    mapping = {
        "active": "bold green",
        "confirmed": "bold green",
        "funded": "bold green",
        "released": "bold green",
        "inactive": "dim",
        "suspended": "bold red",
        "pending": "bold yellow",
        "processing": "yellow",
        "failed": "bold red",
        "expired": "dim red",
        "disputed": "bold magenta",
        "refunded": "cyan",
    }
    return mapping.get(status, "white")


# ── Dashboard Builder ────────────────────────────────────────────

def build_dashboard(data: dict, start_time: float) -> Layout:
    """Build the Rich Layout for the operator dashboard.

    Follows the same patterns as moltfarm autopilot.py:
    Layout with split_column, Panel, Table, colored text, box styles.
    """
    now = datetime.now()
    uptime_s = time.time() - start_time
    uptime_h = int(uptime_s // 3600)
    uptime_m = int((uptime_s % 3600) // 60)
    uptime_sec = int(uptime_s % 60)

    # ── Header ──
    health = data.get("health") or {}
    api_status = health.get("status", "unreachable")
    api_version = health.get("version", "?")

    if api_status == "ok":
        status_indicator = "[bold green]CONNECTED[/]"
    else:
        status_indicator = "[bold red]DISCONNECTED[/]"

    header_text = (
        f"[bold green]AGENTWALLET OPERATOR DASHBOARD[/]  "
        f"API: {status_indicator}  "
        f"v{api_version}  "
        f"[dim]{now.strftime('%Y-%m-%d %H:%M:%S')}[/]"
    )

    # ── Agent Table ──
    agents_data = data.get("agents") or {}
    agents_list = agents_data.get("data", [])
    wallets_data = data.get("wallets") or {}
    wallets_list = wallets_data.get("data", [])

    # Build wallet lookup: agent_id -> wallet info
    wallet_by_agent: dict[str, dict] = {}
    for w in wallets_list:
        agent_id = str(w.get("agent_id", ""))
        if agent_id and agent_id != "None":
            wallet_by_agent[agent_id] = w

    agent_table = Table(
        title="",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold cyan",
        expand=True,
        padding=(0, 1),
    )
    agent_table.add_column("Name", style="bold white", min_width=18)
    agent_table.add_column("Status", justify="center", min_width=10)
    agent_table.add_column("Wallet Address", min_width=20)
    agent_table.add_column("Type", justify="center", min_width=8)
    agent_table.add_column("Reputation", justify="right", min_width=10)
    agent_table.add_column("Public", justify="center", min_width=6)
    agent_table.add_column("Created", justify="center", min_width=12)

    if agents_list:
        for a in agents_list:
            name = a.get("name", "?")
            status = a.get("status", "?")
            status_text = Text(status, style=_status_style(status))
            rep_score = a.get("reputation_score", 0)
            is_public = "Yes" if a.get("is_public") else "No"
            created = a.get("created_at", "?")[:10]

            # Find wallet address for this agent
            agent_id = str(a.get("id", ""))
            wallet_info = wallet_by_agent.get(agent_id, {})
            wallet_addr = _short_addr(wallet_info.get("address", ""), 22)
            wallet_type = wallet_info.get("wallet_type", "--")

            rep_style = "bold green" if rep_score >= 80 else ("yellow" if rep_score >= 50 else "red")
            rep_text = Text(f"{rep_score:.0f}", style=rep_style)

            agent_table.add_row(
                name[:18],
                status_text,
                wallet_addr,
                wallet_type,
                rep_text,
                is_public,
                created,
            )
    else:
        agent_table.add_row(
            "[dim]No agents found[/]", "", "", "", "", "", "",
        )

    # ── Transaction Stats ──
    summary = data.get("summary") or {}
    tx_count = summary.get("tx_count", 0)
    failed_count = summary.get("failed_tx_count", 0)
    active_agents = summary.get("active_agents", 0)
    total_spend = _lamports_to_sol(summary.get("total_spend_lamports", 0))
    total_fees = _lamports_to_sol(summary.get("total_fees_lamports", 0))
    destinations = summary.get("unique_destinations", 0)

    # Derive pending from transactions list
    txs_data = data.get("transactions") or {}
    txs_list = txs_data.get("data", [])
    pending_count = sum(1 for tx in txs_list if tx.get("status") == "pending")
    confirmed_recent = sum(1 for tx in txs_list if tx.get("status") == "confirmed")
    failed_recent = sum(1 for tx in txs_list if tx.get("status") == "failed")

    stats_text = (
        f"[bold cyan]TRANSACTIONS:[/] {tx_count} total | "
        f"[bold yellow]Pending: {pending_count}[/] | "
        f"[bold green]Confirmed: {confirmed_recent}[/] | "
        f"[bold red]Failed: {failed_count}[/]   "
        f"[bold yellow]SPEND:[/] {total_spend} SOL   "
        f"[bold yellow]FEES:[/] {total_fees} SOL   "
        f"[bold cyan]AGENTS:[/] {active_agents} active   "
        f"[bold magenta]DESTINATIONS:[/] {destinations}"
    )

    # ── Recent Transactions Table ──
    tx_table = Table(
        title="",
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold cyan",
        expand=True,
        padding=(0, 1),
    )
    tx_table.add_column("ID", style="dim", min_width=10)
    tx_table.add_column("Type", min_width=10)
    tx_table.add_column("Status", justify="center", min_width=10)
    tx_table.add_column("Amount (SOL)", justify="right", min_width=14)
    tx_table.add_column("Fee (SOL)", justify="right", min_width=12)
    tx_table.add_column("To", min_width=18)
    tx_table.add_column("Memo", min_width=12)
    tx_table.add_column("Created", justify="center", min_width=12)

    if txs_list:
        for tx in txs_list:
            tx_id = _short_id(str(tx.get("id", "")))
            tx_type = tx.get("tx_type", "?")
            status = tx.get("status", "?")
            status_text = Text(status, style=_status_style(status))
            amount = _lamports_to_sol(tx.get("amount_lamports", 0))
            fee = _lamports_to_sol(tx.get("platform_fee_lamports", 0))
            to_addr = _short_addr(tx.get("to_address", ""), 16)
            memo = (tx.get("memo") or "--")[:12]
            created = tx.get("created_at", "?")[11:19]  # HH:MM:SS

            amount_style = "bold green" if status == "confirmed" else ("yellow" if status == "pending" else "red")

            tx_table.add_row(
                tx_id,
                tx_type,
                status_text,
                Text(amount, style=amount_style),
                fee,
                to_addr,
                memo,
                created,
            )
    else:
        tx_table.add_row(
            "[dim]No transactions[/]", "", "", "", "", "", "", "",
        )

    # ── Escrow Summary ──
    escrows_data = data.get("escrows") or {}
    escrows_list = escrows_data.get("data", [])
    escrow_total = escrows_data.get("total", 0)

    # Count by status
    escrow_counts: dict[str, int] = {}
    escrow_value_lamports: int = 0
    for e in escrows_list:
        st = e.get("status", "unknown")
        escrow_counts[st] = escrow_counts.get(st, 0) + 1
        if st in ("funded", "pending"):
            escrow_value_lamports += e.get("amount_lamports", 0)

    escrow_lines = []
    escrow_lines.append(
        f"[bold cyan]Total:[/] {escrow_total}   "
        f"[bold yellow]Active Value:[/] {_lamports_to_sol(escrow_value_lamports)} SOL"
    )

    status_parts = []
    for st, count in sorted(escrow_counts.items()):
        style = _status_style(st)
        status_parts.append(f"[{style}]{st}: {count}[/]")
    if status_parts:
        escrow_lines.append("  ".join(status_parts))
    else:
        escrow_lines.append("[dim]No escrows found[/dim]")

    # Recent escrows mini-table
    if escrows_list:
        escrow_lines.append("")
        for e in escrows_list[:5]:
            eid = _short_id(str(e.get("id", "")))
            est = e.get("status", "?")
            eamt = _lamports_to_sol(e.get("amount_lamports", 0))
            eto = _short_addr(e.get("recipient_address", ""), 14)
            eexp = (e.get("expires_at") or "--")[:10]
            style = _status_style(est)
            escrow_lines.append(
                f"  [{style}]{eid}[/]  {est:<10}  {eamt:>12} SOL  -> {eto}  exp: {eexp}"
            )

    escrow_text = "\n".join(escrow_lines)

    # ── Timer / Footer ──
    fetched = data.get("fetched_at")
    if fetched:
        last_fetch = fetched.strftime("%H:%M:%S")
    else:
        last_fetch = "never"

    wallets_total = wallets_data.get("total", 0)
    agents_total = agents_data.get("total", 0)

    timer_text = (
        f"[bold]Uptime:[/] {uptime_h}h {uptime_m}m {uptime_sec}s   "
        f"[bold]Last Refresh:[/] {last_fetch}   "
        f"[bold]Agents:[/] {agents_total}   "
        f"[bold]Wallets:[/] {wallets_total}   "
        f"[bold]API:[/] {API_URL}"
    )

    # ── Compose Layout ──
    layout = Layout()
    layout.split_column(
        Layout(
            Panel(
                header_text,
                style="bold green",
                expand=True,
            ),
            size=3,
        ),
        Layout(
            Panel(
                agent_table,
                title="[bold white]Agents[/]",
                border_style="cyan",
            ),
            name="agents",
        ),
        Layout(
            Panel(stats_text, title="[bold white]Transaction Stats (30d)[/]", border_style="yellow"),
            size=3,
        ),
        Layout(
            Panel(
                tx_table,
                title="[bold white]Recent Transactions[/]",
                border_style="green",
            ),
            name="transactions",
            size=14,
        ),
        Layout(
            Panel(escrow_text, title="[bold white]Escrow Summary[/]", border_style="magenta"),
            size=10,
        ),
        Layout(
            Panel(timer_text, border_style="dim"),
            size=3,
        ),
    )

    return layout


# ── Main ─────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="AgentWallet Operator Dashboard -- Live monitoring",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_REFRESH_INTERVAL,
        help=f"Refresh interval in seconds (default: {DEFAULT_REFRESH_INTERVAL})",
    )
    args = parser.parse_args()

    interval = max(1, args.interval)
    start_time = time.time()

    print("=" * 55)
    print("  AGENTWALLET OPERATOR DASHBOARD")
    print(f"  Refreshing every {interval}s -- Ctrl+C to stop")
    print("=" * 55)

    client = httpx.Client(timeout=10, follow_redirects=True)

    try:
        # Initial fetch
        data = poll_data(client)

        with Live(
            build_dashboard(data, start_time),
            refresh_per_second=1,
            screen=True,
        ) as live:
            while True:
                try:
                    time.sleep(interval)
                    data = poll_data(client)
                    live.update(build_dashboard(data, start_time))
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    # Build an error display but keep running
                    error_layout = Layout()
                    error_layout.split_column(
                        Layout(
                            Panel(
                                f"[bold red]ERROR: {e}[/]\n[dim]Retrying in {interval}s...[/]",
                                title="[bold red]Dashboard Error[/]",
                                border_style="red",
                            ),
                            size=5,
                        ),
                    )
                    live.update(error_layout)
                    time.sleep(interval)
    except KeyboardInterrupt:
        pass
    finally:
        client.close()

    print("\nDashboard stopped.")


if __name__ == "__main__":
    main()
