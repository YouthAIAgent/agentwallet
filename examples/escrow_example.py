"""
AgentWallet Escrow Example
===========================

Trustless payment flow between two agents using escrow:
  1. Create buyer and seller agents with wallets
  2. Create an escrow contract
  3. Fund the escrow
  4. Release funds to the seller (or refund/dispute)

Prerequisites:
  pip install aw-protocol-sdk
  export AW_API_KEY=aw_live_...

Usage:
  python escrow_example.py
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
    print("  AgentWallet Escrow Example")
    print("=" * 60)

    async with AgentWallet(api_key=API_KEY, base_url=f"{API_BASE}/v1") as aw:

        print("\n[1/5] Creating buyer agent...")
        buyer = await aw.agents.create(
            name="escrow-buyer",
            description="Agent that purchases services",
            capabilities=["purchasing"],
        )
        print(f"  Buyer:  {buyer.id} ({buyer.name})")

        print("\n[2/5] Creating seller agent...")
        seller = await aw.agents.create(
            name="escrow-seller",
            description="Agent that provides services",
            capabilities=["data-analysis"],
        )
        print(f"  Seller: {seller.id} ({seller.name})")

        print("\n[3/5] Creating wallets...")
        buyer_wallet = await aw.wallets.create(
            agent_id=buyer.id,
            label="buyer-wallet",
        )
        seller_wallet = await aw.wallets.create(
            agent_id=seller.id,
            label="seller-wallet",
        )
        print(f"  Buyer wallet:  {buyer_wallet.address}")
        print(f"  Seller wallet: {seller_wallet.address}")

        print("\n[4/5] Creating escrow contract...")
        escrow = await aw.escrow.create(
            funder_wallet=buyer_wallet.id,
            recipient_address=seller_wallet.address,
            amount_sol=0.01,
            conditions={"task": "Analyze dataset and return summary report"},
            expires_in_hours=24,
        )
        print(f"  Escrow ID:     {escrow.id}")
        print(f"  Status:        {escrow.status}")
        print(f"  Amount:        {escrow.amount_lamports} lamports")

        print("\n[5/5] Releasing escrow funds to seller...")
        released = await aw.escrow.release(escrow.id)
        print(f"  Status:        {released.status}")

        print("\n--- Final escrow state ---")
        final = await aw.escrow.get(escrow.id)
        print(f"  Status:     {final.status}")

    print("\n" + "=" * 60)
    print("  Escrow flow complete.")
    print("  Alternatives: aw.escrow.refund(), aw.escrow.dispute()")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
