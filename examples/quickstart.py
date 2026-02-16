"""
AgentWallet Quickstart
======================

Get up and running in 5 minutes:
  1. Register an organization
  2. Generate an API key
  3. Create an AI agent
  4. Create a Solana wallet
  5. Check wallet balance

Prerequisites:
  pip install aw-protocol-sdk

Usage:
  python quickstart.py
"""

import asyncio
import os
import sys

import httpx

API_BASE = os.getenv("AW_API_BASE", "https://api.agentwallet.fun")


async def main():
    print("=" * 60)
    print("  AgentWallet Quickstart")
    print("=" * 60)

    api_key = os.getenv("AW_API_KEY")

    if not api_key:
        print("\n[1/5] Registering a new organization...")
        async with httpx.AsyncClient(base_url=API_BASE, timeout=30) as http:
            reg = await http.post("/v1/auth/register", json={
                "org_name": "QuickstartOrg",
                "email": f"quickstart+{os.urandom(4).hex()}@example.com",
                "password": "SecurePass123!",
            })
            if reg.status_code == 409:
                print("  Email already registered. Set AW_API_KEY to skip.")
                sys.exit(1)
            reg.raise_for_status()
            token_data = reg.json()
            jwt_token = token_data["access_token"]
            org_id = token_data["org_id"]
            print(f"  Org created: {org_id}")

            print("\n[2/5] Generating API key...")
            key_resp = await http.post(
                "/v1/auth/api-keys",
                json={"name": "quickstart-key"},
                headers={"Authorization": f"Bearer {jwt_token}"},
            )
            key_resp.raise_for_status()
            api_key = key_resp.json()["key"]
            print(f"  API key: {api_key[:20]}...")
            print("  Save this! Export as AW_API_KEY for future runs.")
    else:
        print("\n[1/5] Using existing API key from AW_API_KEY env var.")
        print("[2/5] Skipping key generation.")

    from agentwallet import AgentWallet

    async with AgentWallet(api_key=api_key, base_url=f"{API_BASE}/v1") as aw:

        print("\n[3/5] Creating an AI agent...")
        agent = await aw.agents.create(
            name="quickstart-bot",
            description="Demo agent from the quickstart guide",
            capabilities=["trading", "analysis"],
        )
        print(f"  Agent ID:   {agent.id}")
        print(f"  Name:       {agent.name}")
        print(f"  Status:     {agent.status}")

        print("\n[4/5] Creating a Solana wallet for the agent...")
        wallet = await aw.wallets.create(
            agent_id=agent.id,
            wallet_type="agent",
            label="quickstart-wallet",
        )
        print(f"  Wallet ID:  {wallet.id}")
        print(f"  Address:    {wallet.address}")
        print(f"  Type:       {wallet.wallet_type}")

        print("\n[5/5] Checking wallet balance...")
        balance = await aw.wallets.get_balance(wallet.id)
        print(f"  SOL balance: {balance.sol_balance}")
        print(f"  Lamports:    {balance.lamports}")

    print("\n" + "=" * 60)
    print("  Setup complete.")
    print()
    print("  Next steps:")
    print("    - Fund the wallet on Solana devnet")
    print("    - Try escrow_example.py for trustless payments")
    print("    - Try acp_example.py for agent-to-agent commerce")
    print("    - Try swarm_example.py for multi-agent coordination")
    print("    - API docs: https://api.agentwallet.fun/docs")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
