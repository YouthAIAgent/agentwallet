"""
AutoGen + AgentWallet Integration Example
===========================================
Multi-agent negotiation where:
- Buyer Agent: wants to purchase a data analysis service
- Seller Agent: offers the service and delivers results
- Evaluator Agent: independently verifies deliverables

Uses AgentWallet's ACP (Agent Commerce Protocol) for the full lifecycle:
  request → negotiation → fund → deliver → evaluate

Requirements:
    pip install aw-protocol-sdk autogen-agentchat~=0.2

Usage:
    export AW_API_KEY="aw_live_..."
    export OPENAI_API_KEY="sk-..."
    python autogen_example.py
"""

import asyncio
import json
import os

import autogen

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


# ── AgentWallet ACP Functions (registered with AutoGen) ───────

def setup_agents_and_wallets() -> str:
    """Create buyer, seller, and evaluator agents with wallets on AgentWallet."""
    async def _do():
        async with await _client() as aw:
            buyer = await aw.agents.create(
                name="buyer-agent",
                capabilities=["purchasing", "negotiation"],
            )
            seller = await aw.agents.create(
                name="seller-agent",
                capabilities=["data-analysis", "delivery"],
            )
            evaluator = await aw.agents.create(
                name="evaluator-agent",
                capabilities=["quality-assurance", "verification"],
            )

            buyer_wallet = await aw.wallets.create(
                agent_id=buyer.id, label="buyer-wallet",
            )

            return json.dumps({
                "buyer": {"agent_id": buyer.id, "wallet_id": buyer_wallet.id,
                           "address": buyer_wallet.solana_address},
                "seller": {"agent_id": seller.id},
                "evaluator": {"agent_id": evaluator.id},
            }, indent=2)
    return _run(_do())


def create_acp_job(buyer_agent_id: str, seller_agent_id: str,
                   evaluator_agent_id: str) -> str:
    """Create an ACP job — buyer requests a service from seller."""
    async def _do():
        async with await _client() as aw:
            job = await aw.acp.create_job(
                buyer_agent_id=buyer_agent_id,
                seller_agent_id=seller_agent_id,
                evaluator_agent_id=evaluator_agent_id,
                title="Market sentiment analysis for SOL/USDC",
                description="Analyze 7-day sentiment from social media and DEX data",
                price_usdc=25.0,
                requirements={"sources": ["twitter", "dexscreener"], "period": "7d"},
                deliverables={"format": "json_report", "fields": ["sentiment_score", "volume_trend"]},
            )
            return json.dumps({
                "job_id": job.id, "phase": job.phase,
                "price": str(job.price_usdc), "status": "created",
            }, indent=2)
    return _run(_do())


def negotiate_job(job_id: str, seller_agent_id: str) -> str:
    """Seller negotiates terms — agrees with a counter-offer."""
    async def _do():
        async with await _client() as aw:
            job = await aw.acp.negotiate(
                job_id=job_id,
                seller_agent_id=seller_agent_id,
                agreed_terms={
                    "sources": ["twitter", "dexscreener", "reddit"],
                    "period": "7d",
                    "bonus": "include top-10 whale wallets",
                },
                agreed_price_usdc=30.0,  # counter-offer: more sources = higher price
            )
            return json.dumps({
                "job_id": job.id, "phase": job.phase,
                "agreed_price": str(job.agreed_price_usdc),
            }, indent=2)
    return _run(_do())


def fund_job(job_id: str, buyer_agent_id: str) -> str:
    """Buyer funds the job — money goes into escrow."""
    async def _do():
        async with await _client() as aw:
            job = await aw.acp.fund(job_id=job_id, buyer_agent_id=buyer_agent_id)
            return json.dumps({
                "job_id": job.id, "phase": job.phase,
                "funded": True,
            }, indent=2)
    return _run(_do())


def deliver_job(job_id: str, seller_agent_id: str) -> str:
    """Seller delivers the analysis results."""
    async def _do():
        async with await _client() as aw:
            job = await aw.acp.deliver(
                job_id=job_id,
                seller_agent_id=seller_agent_id,
                result_data={
                    "sentiment_score": 0.72,
                    "volume_trend": "increasing",
                    "top_whale_wallets": [
                        "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU",
                        "3yFwqXBfZY4jBVUafQ1YEXw189y2dN3V5KQq9uzBDy1E",
                    ],
                    "summary": "Bullish momentum building, +15% volume in 72h",
                },
                notes="Added Reddit sentiment as bonus — very bullish signal",
            )
            return json.dumps({
                "job_id": job.id, "phase": job.phase,
                "delivered": True,
            }, indent=2)
    return _run(_do())


def evaluate_job(job_id: str, evaluator_agent_id: str) -> str:
    """Evaluator reviews the deliverables and approves payment release."""
    async def _do():
        async with await _client() as aw:
            job = await aw.acp.evaluate(
                job_id=job_id,
                evaluator_agent_id=evaluator_agent_id,
                approved=True,
                evaluation_notes="All deliverables present. Data quality: high.",
                rating=5,
            )
            return json.dumps({
                "job_id": job.id, "phase": job.phase,
                "approved": True, "rating": 5,
            }, indent=2)
    return _run(_do())


def send_memo(job_id: str, sender_agent_id: str, message: str) -> str:
    """Send a signed memo on the ACP job (audit trail)."""
    async def _do():
        async with await _client() as aw:
            memo = await aw.acp.send_memo(
                job_id=job_id,
                sender_agent_id=sender_agent_id,
                memo_type="message",
                content={"text": message},
            )
            return json.dumps({
                "memo_id": memo.id, "type": memo.memo_type,
                "sender": sender_agent_id,
            }, indent=2)
    return _run(_do())


# ── AutoGen Configuration ─────────────────────────────────────

llm_config = {
    "config_list": [{"model": "gpt-4o-mini", "api_key": os.getenv("OPENAI_API_KEY")}],
    "temperature": 0,
}

# The coordinator orchestrates the ACP workflow
coordinator = autogen.AssistantAgent(
    name="Coordinator",
    system_message="""You coordinate an Agent Commerce Protocol (ACP) workflow.

Steps:
1. Call setup_agents_and_wallets() to create buyer, seller, evaluator
2. Call create_acp_job() with the agent IDs
3. Call negotiate_job() — seller agrees with counter-offer
4. Call fund_job() — buyer funds the escrow
5. Call deliver_job() — seller submits results
6. Call evaluate_job() — evaluator approves
7. Summarize the entire workflow

Execute each step in order and report results.""",
    llm_config=llm_config,
)

user_proxy = autogen.UserProxyAgent(
    name="UserProxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config=False,
)

# Register ACP functions with AutoGen
for fn in [setup_agents_and_wallets, create_acp_job, negotiate_job,
           fund_job, deliver_job, evaluate_job, send_memo]:
    coordinator.register_for_llm(description=fn.__doc__)(fn)
    user_proxy.register_for_execution()(fn)


# ── Run ────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not AW_KEY:
        print("Set AW_API_KEY first: export AW_API_KEY='aw_live_...'")
        exit(1)
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY: export OPENAI_API_KEY='sk-...'")
        exit(1)

    print("=" * 60)
    print("  AutoGen + AgentWallet ACP Demo")
    print("  Full lifecycle: request -> negotiate -> fund -> deliver -> evaluate")
    print("=" * 60)

    user_proxy.initiate_chat(
        coordinator,
        message=(
            "Run the complete ACP workflow: set up agents, create a job for "
            "market sentiment analysis, negotiate terms, fund the escrow, "
            "deliver results, and have the evaluator approve the work."
        ),
    )
