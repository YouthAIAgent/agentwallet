"""
CrewAI + AgentWallet Integration Example
=========================================
A crew of AI agents that autonomously manage finances:
- Treasury Agent: creates wallets and monitors balances
- Payment Agent: handles transfers and escrow settlements
- Compliance Agent: enforces spending policies

Requirements:
    pip install aw-protocol-sdk crewai crewai-tools

Usage:
    export AW_API_KEY="aw_live_..."
    python crewai_example.py
"""

import asyncio
import os

from crewai import Agent, Crew, Task
from crewai.tools import BaseTool
from pydantic import Field

# ── AgentWallet async helpers ──────────────────────────────────

AW_BASE = os.getenv("AW_BASE_URL", "https://api.agentwallet.fun/v1")
AW_KEY = os.getenv("AW_API_KEY", "")


def _run_async(coro):
    """Run an async SDK call from sync CrewAI tool context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _get_client():
    from agentwallet import AgentWallet
    return AgentWallet(api_key=AW_KEY, base_url=AW_BASE)


# ── Custom CrewAI Tools ────────────────────────────────────────

class CreateAgentTool(BaseTool):
    name: str = "create_agent"
    description: str = "Register a new AI agent on AgentWallet. Input: agent name."

    def _run(self, agent_name: str) -> str:
        async def _do():
            async with await _get_client() as aw:
                agent = await aw.agents.create(
                    name=agent_name,
                    capabilities=["payments", "escrow"],
                )
                return f"Agent created: {agent.id} ({agent.name})"
        return _run_async(_do())


class CreateWalletTool(BaseTool):
    name: str = "create_wallet"
    description: str = "Create a Solana wallet for an agent. Input: agent_id."

    def _run(self, agent_id: str) -> str:
        async def _do():
            async with await _get_client() as aw:
                wallet = await aw.wallets.create(
                    agent_id=agent_id,
                    wallet_type="agent",
                    label="crew-wallet",
                )
                return (
                    f"Wallet created: {wallet.id}\n"
                    f"Address: {wallet.solana_address}"
                )
        return _run_async(_do())


class CheckBalanceTool(BaseTool):
    name: str = "check_balance"
    description: str = "Check the SOL balance of a wallet. Input: wallet_id."

    def _run(self, wallet_id: str) -> str:
        async def _do():
            async with await _get_client() as aw:
                balance = await aw.wallets.get_balance(wallet_id)
                return f"Balance: {balance.sol_balance} SOL"
        return _run_async(_do())


class TransferSolTool(BaseTool):
    name: str = "transfer_sol"
    description: str = (
        "Transfer SOL between wallets. "
        "Input: 'from_wallet_id,to_address,amount_sol'"
    )

    def _run(self, params: str) -> str:
        from_wallet, to_addr, amount = params.split(",")
        async def _do():
            async with await _get_client() as aw:
                tx = await aw.transactions.transfer_sol(
                    from_wallet=from_wallet.strip(),
                    to_address=to_addr.strip(),
                    amount_sol=float(amount.strip()),
                    memo="crewai-payment",
                )
                return f"Transfer complete: {tx.id} — {tx.status}"
        return _run_async(_do())


class CreateEscrowTool(BaseTool):
    name: str = "create_escrow"
    description: str = (
        "Create an escrow payment. "
        "Input: 'funder_wallet_id,recipient_address,amount_sol'"
    )

    def _run(self, params: str) -> str:
        funder, recipient, amount = params.split(",")
        async def _do():
            async with await _get_client() as aw:
                escrow = await aw.escrow.create(
                    funder_wallet=funder.strip(),
                    recipient_address=recipient.strip(),
                    amount_sol=float(amount.strip()),
                    conditions={"task": "completed"},
                    expires_in_hours=48,
                )
                return (
                    f"Escrow created: {escrow.id}\n"
                    f"Amount: {escrow.amount_sol} SOL — Status: {escrow.status}"
                )
        return _run_async(_do())


class SetPolicyTool(BaseTool):
    name: str = "set_spending_policy"
    description: str = (
        "Set a daily spending limit for an agent. "
        "Input: 'agent_id,max_daily_sol'"
    )

    def _run(self, params: str) -> str:
        agent_id, limit = params.split(",")
        async def _do():
            async with await _get_client() as aw:
                policy = await aw.policies.create(
                    agent_id=agent_id.strip(),
                    policy_type="spending_limit",
                    rules={"max_daily_sol": float(limit.strip())},
                )
                return f"Policy set: {policy.id} — max {limit.strip()} SOL/day"
        return _run_async(_do())


# ── CrewAI Agents ──────────────────────────────────────────────

treasury_agent = Agent(
    role="Treasury Manager",
    goal="Create and manage agent wallets, monitor balances",
    backstory=(
        "You are the chief treasury agent responsible for wallet "
        "infrastructure. You create wallets for new agents and "
        "monitor their balances."
    ),
    tools=[CreateAgentTool(), CreateWalletTool(), CheckBalanceTool()],
    verbose=True,
)

payment_agent = Agent(
    role="Payment Processor",
    goal="Execute SOL transfers and manage escrow payments",
    backstory=(
        "You handle all outgoing payments. You can transfer SOL "
        "directly or create escrow contracts for milestone-based work."
    ),
    tools=[TransferSolTool(), CreateEscrowTool()],
    verbose=True,
)

compliance_agent = Agent(
    role="Compliance Officer",
    goal="Enforce spending policies and risk controls",
    backstory=(
        "You ensure every agent operates within safe financial limits. "
        "You set spending policies before any transfers occur."
    ),
    tools=[SetPolicyTool()],
    verbose=True,
)

# ── Tasks ──────────────────────────────────────────────────────

task_setup = Task(
    description=(
        "1. Register a new AI agent called 'data-scraper-bot'\n"
        "2. Create a Solana wallet for it\n"
        "3. Report the wallet address and agent ID"
    ),
    expected_output="Agent ID and wallet address",
    agent=treasury_agent,
)

task_policy = Task(
    description=(
        "Set a daily spending limit of 5 SOL for the agent created "
        "in the previous task."
    ),
    expected_output="Policy confirmation with ID",
    agent=compliance_agent,
)

task_payment = Task(
    description=(
        "Create an escrow payment of 1 SOL from the agent's wallet "
        "to a recipient address, with the condition that a data "
        "scraping task must be completed."
    ),
    expected_output="Escrow ID and status",
    agent=payment_agent,
)

# ── Crew ───────────────────────────────────────────────────────

crew = Crew(
    agents=[treasury_agent, compliance_agent, payment_agent],
    tasks=[task_setup, task_policy, task_payment],
    verbose=True,
)

if __name__ == "__main__":
    if not AW_KEY:
        print("Set AW_API_KEY environment variable first!")
        print("  export AW_API_KEY='aw_live_...'")
        exit(1)

    result = crew.kickoff()
    print("\n" + "=" * 60)
    print("CREW RESULT:")
    print("=" * 60)
    print(result)
