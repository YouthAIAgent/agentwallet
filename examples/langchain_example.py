"""
LangChain + AgentWallet Integration Example
=============================================
A ReAct agent with AgentWallet tools that can:
- Create wallets and check balances
- Send SOL transfers
- Create and manage escrow payments
- Query analytics

Requirements:
    pip install aw-protocol-sdk langchain langchain-openai

Usage:
    export AW_API_KEY="aw_live_..."
    export OPENAI_API_KEY="sk-..."
    python langchain_example.py
"""

import asyncio
import os
from typing import Optional

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import StructuredTool
from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

# ── Config ─────────────────────────────────────────────────────

AW_BASE = os.getenv("AW_BASE_URL", "https://api.agentwallet.fun/v1")
AW_KEY = os.getenv("AW_API_KEY", "")


def _run(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def _client():
    from agentwallet import AgentWallet
    return AgentWallet(api_key=AW_KEY, base_url=AW_BASE)


# ── Tool Functions ─────────────────────────────────────────────

def create_agent(name: str, capabilities: str = "payments") -> str:
    """Register a new AI agent on AgentWallet Protocol."""
    async def _do():
        async with await _client() as aw:
            agent = await aw.agents.create(
                name=name,
                capabilities=capabilities.split(","),
                description=f"LangChain-managed agent: {name}",
            )
            return f"Agent '{agent.name}' created with ID: {agent.id}"
    return _run(_do())


def create_wallet(agent_id: str, label: str = "main") -> str:
    """Create a Solana wallet for an agent."""
    async def _do():
        async with await _client() as aw:
            wallet = await aw.wallets.create(
                agent_id=agent_id, label=label,
            )
            return (
                f"Wallet created!\n"
                f"  ID: {wallet.id}\n"
                f"  Address: {wallet.solana_address}\n"
                f"  Label: {label}"
            )
    return _run(_do())


def check_balance(wallet_id: str) -> str:
    """Check the SOL balance of a wallet."""
    async def _do():
        async with await _client() as aw:
            bal = await aw.wallets.get_balance(wallet_id)
            return f"Wallet {wallet_id}: {bal.sol_balance} SOL"
    return _run(_do())


def list_agents(limit: int = 10) -> str:
    """List all registered agents."""
    async def _do():
        async with await _client() as aw:
            result = await aw.agents.list(limit=limit)
            lines = [f"Total agents: {result.total}"]
            for a in result.data:
                lines.append(f"  - {a.name} (ID: {a.id}, status: {a.status})")
            return "\n".join(lines)
    return _run(_do())


def transfer_sol(from_wallet_id: str, to_address: str, amount_sol: float,
                 memo: Optional[str] = None) -> str:
    """Transfer SOL from a wallet to a Solana address."""
    async def _do():
        async with await _client() as aw:
            tx = await aw.transactions.transfer_sol(
                from_wallet=from_wallet_id,
                to_address=to_address,
                amount_sol=amount_sol,
                memo=memo or "langchain-transfer",
            )
            return f"Transfer {tx.id}: {amount_sol} SOL — status: {tx.status}"
    return _run(_do())


def create_escrow(funder_wallet_id: str, recipient_address: str,
                  amount_sol: float) -> str:
    """Create an escrow contract to hold SOL until conditions are met."""
    async def _do():
        async with await _client() as aw:
            escrow = await aw.escrow.create(
                funder_wallet=funder_wallet_id,
                recipient_address=recipient_address,
                amount_sol=amount_sol,
                conditions={"approval": "required"},
            )
            return (
                f"Escrow {escrow.id} created!\n"
                f"  Amount: {escrow.amount_sol} SOL\n"
                f"  Status: {escrow.status}"
            )
    return _run(_do())


def set_spending_policy(agent_id: str, max_daily_sol: float) -> str:
    """Set a daily spending limit for an agent."""
    async def _do():
        async with await _client() as aw:
            policy = await aw.policies.create(
                agent_id=agent_id,
                policy_type="spending_limit",
                rules={"max_daily_sol": max_daily_sol},
            )
            return f"Policy {policy.id}: max {max_daily_sol} SOL/day for agent {agent_id}"
    return _run(_do())


# ── Build LangChain Tools ─────────────────────────────────────

tools = [
    StructuredTool.from_function(create_agent, name="create_agent",
        description="Register a new AI agent. Args: name, capabilities (comma-separated)"),
    StructuredTool.from_function(create_wallet, name="create_wallet",
        description="Create a Solana wallet for an agent. Args: agent_id, label"),
    StructuredTool.from_function(check_balance, name="check_balance",
        description="Check SOL balance of a wallet. Args: wallet_id"),
    StructuredTool.from_function(list_agents, name="list_agents",
        description="List all registered agents. Args: limit"),
    StructuredTool.from_function(transfer_sol, name="transfer_sol",
        description="Transfer SOL. Args: from_wallet_id, to_address, amount_sol, memo"),
    StructuredTool.from_function(create_escrow, name="create_escrow",
        description="Create escrow payment. Args: funder_wallet_id, recipient_address, amount_sol"),
    StructuredTool.from_function(set_spending_policy, name="set_spending_policy",
        description="Set daily spending limit. Args: agent_id, max_daily_sol"),
]

# ── ReAct Agent ────────────────────────────────────────────────

PROMPT = PromptTemplate.from_template("""You are a financial AI assistant with access to AgentWallet Protocol.
You can create agents, manage wallets, transfer SOL, and set up escrow payments on Solana.

You have access to the following tools:
{tools}

Use this format:
Question: the input question
Thought: think about what to do
Action: the tool name
Action Input: the tool input
Observation: the tool result
... (repeat Thought/Action/Observation as needed)
Thought: I now know the final answer
Final Answer: the final answer

Tool names: {tool_names}

Question: {input}
{agent_scratchpad}""")


def main():
    if not AW_KEY:
        print("Set AW_API_KEY environment variable first!")
        return

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    agent = create_react_agent(llm, tools, PROMPT)
    executor = AgentExecutor(agent=agent, tools=tools, verbose=True,
                             handle_parsing_errors=True)

    # Example queries to try:
    queries = [
        "Create a new AI agent called 'research-bot' with capabilities: payments, analytics",
        "List all my agents",
        "Create a wallet for the research-bot agent and check its balance",
    ]

    for q in queries:
        print(f"\n{'='*60}")
        print(f"QUERY: {q}")
        print("=" * 60)
        result = executor.invoke({"input": q})
        print(f"\nRESULT: {result['output']}")


if __name__ == "__main__":
    main()
