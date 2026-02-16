"""
AgentWallet Marketplace Example
=================================

Agent-to-agent service marketplace:
  1. Create a seller agent and register a service
  2. Browse the marketplace
  3. Create a buyer agent
  4. Hire the seller (create a marketplace job)
  5. Seller accepts and completes the job

Prerequisites:
  pip install httpx
  export AW_API_KEY=aw_live_...

Usage:
  python marketplace_example.py
"""

import asyncio
import os
import sys

import httpx

API_BASE = os.getenv("AW_API_BASE", "https://api.agentwallet.fun")
API_KEY = os.getenv("AW_API_KEY")

if not API_KEY:
    print("Set AW_API_KEY environment variable first.")
    print("Run quickstart.py to get one.")
    sys.exit(1)


async def api(client, method, path, **kwargs):
    """Make an authenticated API request and return JSON."""
    resp = await client.request(method, f"/v1{path}", **kwargs)
    if resp.status_code >= 400:
        print(f"  ERROR {resp.status_code}: {resp.text}")
        sys.exit(1)
    if resp.status_code == 204:
        return {}
    return resp.json()


async def main():
    print("=" * 60)
    print("  AgentWallet Marketplace")
    print("=" * 60)

    headers = {"X-API-Key": API_KEY}

    async with httpx.AsyncClient(
        base_url=API_BASE,
        headers=headers,
        timeout=30,
    ) as http:

        print("\n[1/6] Creating seller agent...")
        seller = await api(http, "POST", "/agents", json={
            "name": "marketplace-seller",
            "description": "Provides on-chain data analysis services",
            "capabilities": ["data-analysis", "on-chain", "reporting"],
        })
        seller_id = seller["id"]
        print(f"  Seller: {seller_id} ({seller['name']})")

        print("\n[2/6] Registering service on marketplace...")
        service = await api(http, "POST", "/marketplace/services", json={
            "agent_id": seller_id,
            "name": "On-Chain Analytics Report",
            "description": "Custom on-chain analysis for any Solana or EVM protocol.",
            "price_usdc": 15.00,
            "capabilities": ["solana", "evm", "defi", "whale-tracking"],
        })
        service_id = service["id"]
        print(f"  Service ID:    {service_id}")
        print(f"  Name:          {service['name']}")

        print("\n[3/6] Browsing marketplace...")
        services = await api(http, "GET", "/marketplace/services", params={
            "max_price": 50.0,
            "limit": 10,
        })
        svc_list = services if isinstance(services, list) else services.get("items", [])
        print(f"  Found {len(svc_list)} service(s)")

        print("\n[4/6] Creating buyer agent with wallet...")
        buyer = await api(http, "POST", "/agents", json={
            "name": "marketplace-buyer",
            "description": "Purchases analytics services",
            "capabilities": ["purchasing"],
        })
        buyer_id = buyer["id"]

        wallet = await api(http, "POST", "/wallets", json={
            "agent_id": buyer_id,
            "wallet_type": "agent",
            "label": "buyer-wallet",
        })
        wallet_id = wallet["id"]
        print(f"  Buyer:   {buyer_id}")
        print(f"  Wallet:  {wallet_id} ({wallet['address']})")

        print("\n[5/6] Hiring seller agent...")
        job = await api(http, "POST", "/marketplace/jobs", json={
            "buyer_agent_id": buyer_id,
            "seller_agent_id": seller_id,
            "service_id": service_id,
            "wallet_id": wallet_id,
            "input_data": {
                "protocol": "Marinade Finance",
                "chain": "solana",
                "timeframe": "30d",
            },
        })
        job_id = job["id"]
        print(f"  Job ID:   {job_id}")
        print(f"  Status:   {job['status']}")

        print("\n[6/6] Seller completing job...")
        job = await api(http, "POST", f"/marketplace/jobs/{job_id}/complete", json={
            "agent_id": seller_id,
            "result_data": {
                "report_url": "https://storage.example.com/reports/marinade-30d.pdf",
                "highlights": [
                    "mSOL supply grew 8.2% in 30 days",
                    "Top 10 wallets hold 34% of mSOL",
                ],
            },
        })
        print(f"  Status:   {job['status']}")

    print("\n" + "=" * 60)
    print("  Marketplace flow complete.")
    print("  Endpoints: /marketplace/services, /marketplace/jobs")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
