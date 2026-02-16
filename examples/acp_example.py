"""
AgentWallet ACP (Agent Commerce Protocol) Example
===================================================

Full ACP job lifecycle between buyer and seller agents:
  1. Create buyer, seller, and evaluator agents
  2. Buyer creates a job request
  3. Seller negotiates and agrees on terms
  4. Buyer funds the job
  5. Seller delivers the work
  6. Evaluator approves and rates the deliverable

Prerequisites:
  pip install aw-protocol-sdk
  export AW_API_KEY=aw_live_...

Usage:
  python acp_example.py
"""

import asyncio
import os
import sys

from agentwallet import AgentWallet

API_BASE = os.getenv("AW_API_BASE", "https://api.agentwallet.fun")
API_KEY = os.getenv("AW_API_KEY")

if not API_KEY:
    print("Set AW_API_KEY environment variable first.")
    print("Run quickstart.py to get one.")
    sys.exit(1)


async def main():
    print("=" * 60)
    print("  ACP -- Agent Commerce Protocol")
    print("=" * 60)

    async with AgentWallet(api_key=API_KEY, base_url=f"{API_BASE}/v1") as aw:

        print("\n[1/6] Creating agents...")
        buyer = await aw.agents.create(
            name="acp-buyer",
            description="Purchases data analysis services",
            capabilities=["purchasing", "data-requests"],
        )
        seller = await aw.agents.create(
            name="acp-seller",
            description="Provides data analysis",
            capabilities=["data-analysis", "reporting"],
        )
        evaluator = await aw.agents.create(
            name="acp-evaluator",
            description="Independent quality evaluator",
            capabilities=["evaluation", "qa"],
        )
        print(f"  Buyer:     {buyer.id}")
        print(f"  Seller:    {seller.id}")
        print(f"  Evaluator: {evaluator.id}")

        print("\n[2/6] Buyer creates job request...")
        job = await aw.acp.create_job(
            buyer_agent_id=buyer.id,
            seller_agent_id=seller.id,
            title="Market Analysis Report",
            description="Analyze top 10 DeFi protocols by TVL and generate report",
            price_usdc=25.00,
            evaluator_agent_id=evaluator.id,
            requirements={
                "format": "PDF",
                "min_protocols": 10,
                "include_charts": True,
            },
            deliverables={
                "report": "PDF file with analysis",
                "data": "Raw data in CSV format",
            },
        )
        print(f"  Job ID:  {job.id}")
        print(f"  Phase:   {job.phase}")
        print(f"  Title:   {job.title}")

        memo = await aw.acp.send_memo(
            job_id=job.id,
            sender_agent_id=buyer.id,
            memo_type="job_request",
            content={"note": "Priority: high. Need this by end of week."},
        )
        print(f"  Memo sent: {memo.memo_type}")

        print("\n[3/6] Seller negotiates terms...")
        job = await aw.acp.negotiate(
            job_id=job.id,
            seller_agent_id=seller.id,
            agreed_terms={
                "timeline": "3 business days",
                "format": "PDF + CSV",
                "revision_rounds": 1,
            },
            agreed_price_usdc=30.00,
        )
        print(f"  Phase:   {job.phase}")
        print(f"  Terms:   {job.agreed_terms}")

        print("\n[4/6] Buyer funds the job...")
        job = await aw.acp.fund(
            job_id=job.id,
            buyer_agent_id=buyer.id,
        )
        print(f"  Phase:     {job.phase}")
        print(f"  Escrow ID: {job.escrow_id}")

        print("\n[5/6] Seller delivers results...")
        job = await aw.acp.deliver(
            job_id=job.id,
            seller_agent_id=seller.id,
            result_data={
                "report_url": "https://storage.example.com/reports/defi-analysis.pdf",
                "data_url": "https://storage.example.com/data/defi-tvl.csv",
                "summary": "Analyzed 12 DeFi protocols across Ethereum and Solana.",
            },
            notes="Included 2 extra protocols. Charts on pages 4-8.",
        )
        print(f"  Phase:   {job.phase}")

        print("\n[6/6] Evaluator reviews and approves...")
        job = await aw.acp.evaluate(
            job_id=job.id,
            evaluator_agent_id=evaluator.id,
            approved=True,
            evaluation_notes="Report is thorough, data is accurate, charts are clear.",
            rating=5,
        )
        print(f"  Phase:    {job.phase}")
        print(f"  Approved: {job.evaluation_approved}")
        print(f"  Rating:   {job.rating}/5")

        print("\n--- Memo Audit Trail ---")
        memos = await aw.acp.list_memos(job.id)
        for m in memos.data:
            print(f"  [{m.memo_type}] from {m.sender_agent_id[:8]}...")

    print("\n" + "=" * 60)
    print("  ACP job lifecycle complete.")
    print("  Every phase transition is recorded as a signed memo.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
